use pyo3::prelude::*;
use pyo3::types::PyDict;
use rusqlite::{params, Connection};
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use crate::routes;

#[derive(Debug, Deserialize, Serialize, Clone)]
struct LatLon {
    lat: f64,
    lon: f64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct CategoryConfig {
    start: Option<usize>,
    finish: Option<usize>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct StartsFinishes {
    categories: HashMap<String, CategoryConfig>,
    starts: Vec<LatLon>,
    finishes: Vec<LatLon>,
}

#[pyclass(unsendable)]
pub struct RouteEngine {
    conn: Connection,
    category_cache: HashMap<String, (Vec<routes::Point>, i64)>,
    path_cache: HashMap<(i64, Vec<i32>, i64), f64>,
}

#[pymethods]
impl RouteEngine {
    #[new]
    fn new(db_path: String) -> PyResult<Self> {
        let conn = Connection::open(db_path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        let _ = conn.execute("PRAGMA journal_mode=WAL", []);

        Ok(Self {
            conn,
            category_cache: HashMap::new(),
            path_cache: HashMap::new(),
        })
    }

    fn invalidate_cache(&mut self, category_name: Option<String>) -> PyResult<()> {
        if (category_name.is_none()) {
            self.category_cache.clear();
        } else {
            self.category_cache.remove(&category_name.unwrap_or_default());
        }
        self.path_cache.clear();
        Ok(())
    }
    
    fn calculate_category_route(
        &mut self,
        category_name: String
    ) -> PyResult<(Vec<routes::Point>, i64)> {
        if let Some(cached) = self.category_cache.get(&category_name) {
            return Ok(cached.clone());
        }

        let mut stmt = self.conn.prepare(
            "SELECT MAX(c2.id) AS id, c2.lat, c2.lon, c2.code
             FROM controls c1
             JOIN control_associations cc ON c1.id = cc.control_id
             JOIN categories cat ON cat.id = cc.category_id
             JOIN controls c2 ON c1.code = c2.code
             WHERE cat.name = ?1 AND c2.lat IS NOT NULL AND c2.lon IS NOT NULL
             GROUP BY c2.code;"
        ).map_err(db_err)?;

        let rows = stmt.query_map(params![category_name], |row| {
            Ok(routes::Point { id: row.get(0)?, lat: row.get(1)?, lon: row.get(2)? })
        }).map_err(db_err)?;

        let mut points = Vec::new();
        for row in rows { points.push(row.map_err(db_err)?); }
        if points.is_empty() { return Ok((vec![], 0)); }

        let (start, finish, (sid, fid)) = self.resolve_cat_sf(&self.get_starts_finishes()?, &category_name)?;

        if sid == -1 || fid == -1 {
            return Ok((vec![], 0));
        }

        let mut input_points = vec![start.clone()];

        let mut points_map = HashMap::new();
        points_map.insert(9998, start.clone());
        points_map.insert(9999, finish.clone());

        for p in points {
            points_map.insert(p.id, p.clone());
            input_points.push(p);
        }
        input_points.push(finish);

        let (best_ids, length_km) = routes::optimal_route(input_points)?;

        let result_points: Vec<routes::Point> = best_ids.iter()
            .filter_map(|id| points_map.get(id).cloned())
            .collect();

        let length_m = (length_km * 1000.0) as i64;
        self.category_cache.insert(category_name, (result_points.clone(), length_m));

        Ok((result_points, length_m))
    }
    
    fn calculate_runner_route(
        &mut self,
        runner_id: i32
    ) -> PyResult<f64> {
        let mut stmt = self.conn.prepare(
            "SELECT cat.name, c.id, c.lat, c.lon FROM runners r
             JOIN categories cat ON r.category_id = cat.id
             JOIN punches p ON r.si = p.si
             JOIN controls c ON p.code = c.code
             WHERE r.id = ?1 AND c.lat IS NOT NULL
             ORDER BY p.id"
        ).map_err(db_err)?;

        let mut cat_name = String::new();
        let mut path_ids = Vec::new();
        let mut coords = Vec::new();

        let rows = stmt.query_map(params![runner_id], |row| {
            let name: String = row.get(0)?;
            Ok((name, row.get::<_, i32>(1)?, row.get::<_, f64>(2)?, row.get::<_, f64>(3)?))
        }).map_err(db_err)?;

        for row in rows {
            let (name, id, lat, lon) = row.map_err(db_err)?;
            cat_name = name;
            path_ids.push(id);
            coords.push((lat, lon));
        }

        if path_ids.is_empty() { return Ok(0.0); }

        let (start, finish, (sid, fid)) = self.resolve_cat_sf(&self.get_starts_finishes()?, &cat_name)?;

        if sid == -1 || fid == -1 {
            return Ok(0.0);
        }

        if let Some(&dist) = self.path_cache.get(&(sid, path_ids.clone(), fid)) {
            return Ok(dist);
        }

        let mut total_dist = 0.0;
        let mut last_point = start.clone();

        for (p_lat, p_lon) in coords {
            let point = routes::Point { id: 0, lat: p_lat, lon: p_lon };
            total_dist += routes::point_dist(last_point, point.clone())?;
            last_point = point;
        }
        total_dist += routes::point_dist(last_point, finish)?;

        self.path_cache.insert((sid, path_ids.clone(), fid), total_dist);
        Ok(total_dist)
    }
}
impl RouteEngine {
    fn get_starts_finishes(&self) -> PyResult<StartsFinishes> {
        let mut stmt = self.conn.prepare(
            "SELECT value FROM basicinfo WHERE key = 'map_starts_finishes' LIMIT 1"
        ).map_err(db_err)?;

        let json_str: String = stmt.query_row([], |row| row.get(0)).map_err(db_err)?;

        serde_json::from_str(&json_str).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON Parse Error: {}", e))
        })
    }

    fn resolve_cat_sf(&self, sf: &StartsFinishes, cat_name: &str) -> PyResult<(routes::Point, routes::Point, (i64, i64))> {
        let config = sf.categories.get(cat_name)
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>(format!("Category {} not found", cat_name)))?;

        if config.start.is_none() || config.finish.is_none() {
            return Ok((routes::Point {id: 9998, lat: 0.0, lon: 0.0}, routes::Point {id: 9999, lat: 0.0, lon: 0.0}, (-1, -1)));
        }

        let start = sf.starts.get(config.start.unwrap())
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyIndexError, _>("Start index out of bounds"))?;

        let finish = sf.finishes.get(config.finish.unwrap())
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyIndexError, _>("Finish index out of bounds"))?;

        Ok((routes::Point {id: 9998, lat: start.lat, lon: start.lon}, routes::Point {id: 9999, lat: finish.lat, lon: finish.lon}, (config.start.unwrap() as i64, config.finish.unwrap() as i64)))
    }
}

fn db_err(e: rusqlite::Error) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string())
}
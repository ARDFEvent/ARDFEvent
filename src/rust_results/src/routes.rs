use pyo3::prelude::*;
use itertools::Itertools;

#[pyclass]
#[derive(Clone)]
pub struct Point {
    #[pyo3(get, set)]
    id: i32,
    #[pyo3(get, set)]
    lat: f64,
    #[pyo3(get, set)]
    lon: f64,
}

#[pymethods]
impl Point {
    #[new]
    fn new(id: i32, lat: f64, lon: f64) -> Self {
        Point { id, lat, lon }
    }
}

#[pyfunction]
pub fn point_dist(p1: Point, p2: Point) -> PyResult<f64> {
    Ok(haversine_dist(&p1, &p2))
}

fn haversine_dist(p1: &Point, p2: &Point) -> f64 {
    let r = 6371.0;
    let d_lat = (p2.lat - p1.lat).to_radians();
    let d_lon = (p2.lon - p1.lon).to_radians();

    let a = (d_lat / 2.0).sin().powi(2)
        + p1.lat.to_radians().cos() * p2.lat.to_radians().cos() * (d_lon / 2.0).sin().powi(2);

    let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());
    r * c
}

#[pyfunction]
pub fn optimal_route(points: Vec<Point>) -> PyResult<(Vec<i32>, f64)> {
    let n = points.len();
    if n < 2 {
        let single_id = if n == 1 { vec![points[0].id] } else { vec![] };
        return Ok((single_id, 0.0));
    }

    let start_point = &points[0];
    let end_point = &points[n - 1];

    let mid_indices: Vec<usize> = (1..n - 1).collect();

    let mut min_dist = f64::MAX;
    let mut best_id_path = Vec::new();

    for p_indices in mid_indices.iter().copied().permutations(mid_indices.len()) {
        let mut current_dist = 0.0;
        let mut current_id_path = vec![start_point.id];

        let mut prev = start_point;
        for &idx in &p_indices {
            let curr = &points[idx];
            current_dist += haversine_dist(prev, curr);
            current_id_path.push(curr.id);
            prev = curr;
        }

        current_dist += haversine_dist(prev, end_point);
        current_id_path.push(end_point.id);

        if current_dist < min_dist {
            min_dist = current_dist;
            best_id_path = current_id_path;
        }
    }

    Ok((best_id_path, min_dist))
}
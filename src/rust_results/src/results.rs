use pyo3::prelude::*;
use chrono::{DateTime, Utc};
use std::collections::{HashMap, HashSet};

struct BasicInfo {
    key: String,
    value: String,
}

#[derive(Clone)]
struct Control {
    code: i32,
    name: String,
}

struct Person {
    id: i64,
    name: String,
    club: String,
    si: i64,
    reg: String,
    startlist_time: Option<DateTime<Utc>>,
    manual_dns: bool,
    manual_disk: bool,
}

struct Punch {
    code: i32,
    time: DateTime<Utc>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct OResult {
    #[pyo3(get, set)]
    pub id: u64,
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub reg: String,
    #[pyo3(get, set)]
    pub si: i64,
    #[pyo3(get, set)]
    pub tx: i32,
    #[pyo3(get, set)]
    pub time: i64,
    #[pyo3(get, set)]
    pub status: String,
    #[pyo3(get, set)]
    pub order: Vec<(String, DateTime<Utc>, String)>,
    #[pyo3(get, set)]
    pub place: i32,
    #[pyo3(get, set)]
    pub club: String,
    #[pyo3(get, set)]
    pub start: Option<DateTime<Utc>>,
    #[pyo3(get, set)]
    pub finish: Option<DateTime<Utc>>,
}

#[pymethods]
impl OResult {
    #[new]
    fn new(
        id: u64,
        name: String,
        reg: String,
        si: i64,
        tx: i32,
        time: i64,
        status: String,
        order: Vec<(String, DateTime<Utc>, String)>,
        club: String,
        start: Option<i64>,
        finish: Option<i64>,
    ) -> Self {
        OResult {
            id,
            name,
            reg,
            si,
            tx,
            time,
            status,
            order,
            place: 0,
            club,
            start: start.map(|ts| DateTime::from_timestamp(ts, 0).unwrap_or_default()),
            finish: finish.map(|ts| DateTime::from_timestamp(ts, 0).unwrap_or_default()),
        }
    }
}

#[pyfunction]
pub fn calculate_category(_py: Python, _db_path: String, _name: String, _include_unknown: bool, now: i64) -> PyResult<Vec<OResult>> {

    let mut results: Vec<OResult> = Vec::new();

    let conn = rusqlite::Connection::open(&_db_path)
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}"))
        })?;

    let mut _basicinfo_stmt = conn.prepare("SELECT key, value from basicinfo;")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;

    let _basicinfo_vec: Vec<BasicInfo> = _basicinfo_stmt.query_map([], |row| {
        Ok(BasicInfo {
            key: row.get(0)?,
            value: row.get(1)?,
        })
    })
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?
        .filter_map(Result::ok)
        .collect();
    let _basicinfo: HashMap<String, String> = _basicinfo_vec.into_iter().map(|bi| (bi.key, bi.value)).collect();

    let mut _allcontrols_stmt = conn.prepare("SELECT name, code from controls;")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;

    let _allcontrols_vec: Vec<Control> = _allcontrols_stmt.query_map([], |row| {
        Ok(Control {
            name: row.get(0)?,
            code: row.get(1)?,
        })
    })
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?
        .filter_map(Result::ok)
        .collect();
    let _allcontrols: HashMap<i32, String> = _allcontrols_vec.into_iter().map(|c| (c.code, c.name)).collect();

    let mut _loccontrols_stmt = conn.prepare("SELECT name, code from controls where id in (SELECT control_id from control_associations where category_id in (SELECT id from categories where name = ?1));")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;
    let _loccontrols_vec: Vec<Control> = _loccontrols_stmt.query_map([&_name], |row| {
        Ok(Control {
            name: row.get(0)?,
            code: row.get(1)?,
        })
    })
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?
        .filter_map(Result::ok)
        .collect();

    let _loccontrols: HashMap<i32, String> = _loccontrols_vec.into_iter().map(|c| (c.code, c.name)).collect();

    let mut _mandcontrols_stmt = conn.prepare("SELECT name, code from controls where mandatory = 1 and id in (SELECT control_id from control_associations where category_id in (SELECT id from categories where name = ?1));")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;
    let _mandcontrols_vec: Vec<Control> = _mandcontrols_stmt.query_map([&_name], |row| {
        Ok(Control {
            name: row.get(0)?,
            code: row.get(1)?,
        })
    })
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?
        .filter_map(Result::ok)
        .collect();

    let _mandcontrols: HashSet<i32> = _mandcontrols_vec.into_iter().map(|c| c.code).collect();

    let mut category_id_query = conn.prepare("SELECT id from categories where name = ?1;")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;
    let category_id: Option<i64> = category_id_query.query_row([&_name], |row| row.get(0)).ok();

    let mut persons_stmt = conn.prepare("SELECT name, club, si, reg, startlist_time, manual_dns, manual_disk, id from runners where category_id = ?1;")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;
    let persons: Vec<Person> = if let Some(cat_id) = category_id {
        persons_stmt.query_map([cat_id], |row| {
            Ok(Person {
                name: row.get(0)?,
                club: row.get(1)?,
                si: row.get(2)?,
                reg: row.get(3)?,
                startlist_time: row.get(4).ok(),
                manual_dns: row.get(5)?,
                manual_disk: row.get(6)?,
                id: row.get(7)?,
            })
        })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?
            .filter_map(Result::ok)
            .collect()
    } else {
        Vec::new()
    };

    let mut punches_map: HashMap<i64, Vec<Punch>> = HashMap::new();
    if let Some(cat_id) = category_id {
        let mut punches_stmt = conn.prepare("SELECT p.si, p.code, p.time FROM punches p JOIN runners r ON p.si = r.si WHERE r.category_id = ?1 ORDER BY p.si, p.time;")
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?;
        let _all_punches: Vec<(i64, i32, DateTime<Utc>)> = punches_stmt.query_map([cat_id], |row| {
            Ok((row.get(0)?, row.get(1)?, row.get(2)?))
        })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Database error: {e}")))?
            .filter_map(Result::ok)
            .collect();

        for (si, code, time) in _all_punches {
            punches_map.entry(si).or_insert_with(Vec::new).push(Punch { code, time });
        }
    }

    fn push_result(
        results: &mut Vec<OResult>,
        per: &Person,
        status: &str,
        tx: i32,
        time: i64,
        order: Vec<(String, DateTime<Utc>, String)>,
        place: i32,
        start: Option<DateTime<Utc>>,
        finish: Option<DateTime<Utc>>,
    ) {
        results.push(OResult {
            id: per.id as u64,
            name: per.name.clone(),
            reg: per.reg.clone(),
            si: per.si,
            tx,
            time,
            status: status.to_string(),
            order,
            place,
            club: per.club.clone(),
            start,
            finish,
        });
    }

    for per in &persons {
        if per.manual_dns {
            push_result(&mut results, per, "DNS", 0, 0, vec![], 0, None, None);
            continue;
        }
        if per.manual_disk {
            push_result(&mut results, per, "DSQ", 0, 0, vec![], 0, None, None);
            continue;
        }

        let default_vec_punch: &Vec<Punch> = &Vec::new();
        let punches_ref: &Vec<Punch> = punches_map.get(&per.si).unwrap_or(default_vec_punch);
        let punches: &Vec<Punch> = punches_ref;

        let mut tx: i32 = 0;
        let mut mandatory_cnt: i32 = 0;
        let mut start = per.startlist_time;
        let mut finish: Option<DateTime<Utc>> = None;
        let mut order: Vec<(String, DateTime<Utc>, String)> = Vec::new();

        let mut loccontrols = _loccontrols.clone();
        let mut mandcontrols = _mandcontrols.clone();

        if punches.is_empty() {
            if _include_unknown {
                push_result(&mut results, per, "?", 0, if start.is_none() { 0 } else { now - start.unwrap().timestamp() }, vec![], 0, start, None);
            }
            continue;
        }

        for punch in punches {
            if punch.code == 1000 {
                start = Some(punch.time);
            } else if punch.code == 1001 {
                finish = Some(punch.time);
            }

            if let Some(name) = loccontrols.remove(&punch.code) {
                tx += 1;
                order.push((name, punch.time, "OK".to_string()));
            } else if let Some(name) = _allcontrols.get(&punch.code) {
                order.push((format!("{}+", name), punch.time, "AP".to_string()));
            }

            if mandcontrols.remove(&punch.code) {
                mandatory_cnt += 1;
            }
        }

        let mut status = "OK";

        if start.is_none() {
            if let Some(date_tzero) = _basicinfo.get("DATE_TIME") {
                start = Some(DateTime::parse_from_rfc3339(date_tzero.as_str()).unwrap().to_utc());
            } else {
                push_result(&mut results, per, "DNS", 0, 0, vec![], 0, None, finish);
            }
        }

        if finish.is_none() {
            push_result(&mut results, per, "DNF", tx, 0, vec![], 0, start, None);
            continue;
        }

        if (mandatory_cnt < _mandcontrols.len() as i32 || tx - mandatory_cnt < 1) && status == "OK" {
            status = "MP";
        } else if let Some(limit_value) = _basicinfo.get("LIMIT").or(_basicinfo.get("limit")) {
            if limit_value.parse::<i64>().unwrap_or_default() * 60 < finish.unwrap().timestamp() - start.unwrap().timestamp() {
                status = "OVT";
            }
        }

        push_result(&mut results, per, status, tx,  if status == "OK" || status == "MP" || status == "OVT" {finish.unwrap().timestamp() - start.unwrap().timestamp()} else {0}, order, 0, start, finish);
    }

    let mut res = results.clone();
    let mut ok = res.iter_mut().filter(|r| r.status == "OK").collect::<Vec<&mut OResult>>();
    let mut running = results.iter().filter(|r| r.status == "?").collect::<Vec<&OResult>>();
    let mut nok = results.iter().filter(|r| r.status != "OK" && r.status != "?").collect::<Vec<&OResult>>();

    ok.sort_by_key(|x| (-x.tx, x.time, x.name.clone()));
    running.sort_by_key(|x| (-x.time, x.name.clone()));
    nok.sort_by_key(|x| (x.status.clone(), x.name.clone()));

    let mut i = 0;
    let mut lastplace = 0;
    let mut lasttime = 0;
    let mut lasttx = 0;

    let mut ok_wp = Vec::new();

    for run in ok {
        i += 1;
        let mut r = run.clone();
        if r.time == lasttime && r.tx == lasttx {
            r.place = lastplace;
        } else {
            r.place = i;
        }
        lasttime = r.time;
        lasttx = r.tx;
        lastplace = r.place;

        ok_wp.push(r);
    }

    let mut final_results: Vec<OResult> = Vec::new();
    final_results.append(&mut ok_wp.into_iter().map(|r| r.clone()).collect::<Vec<OResult>>());
    final_results.append(&mut running.into_iter().map(|r| r.clone()).collect::<Vec<OResult>>());
    final_results.append(&mut nok.into_iter().map(|r| r.clone()).collect::<Vec<OResult>>());

    Ok(final_results)
}
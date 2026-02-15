use pyo3::prelude::*;

mod results;
mod routes;

#[pymodule]
fn ardfevent_rust(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    let results_submodule = PyModule::new(py, "ardfevent_rust.results")?;
    results_submodule.add_function(wrap_pyfunction!(crate::results::calculate_category, &results_submodule)?)?;
    results_submodule.add_class::<crate::results::OResult>()?;
    m.add("results", &results_submodule)?;
    py.import("sys")?
        .getattr("modules")?
        .set_item("ardfevent_rust.results", &results_submodule)?;

    let routes_submodule = PyModule::new(py, "ardfevent_rust.routes")?;
    routes_submodule.add_function(wrap_pyfunction!(crate::routes::point_dist, &routes_submodule)?)?;
    routes_submodule.add_function(wrap_pyfunction!(crate::routes::optimal_route, &routes_submodule)?)?;
    routes_submodule.add_class::<crate::routes::Point>()?;
    m.add("routes", &routes_submodule)?;
    py.import("sys")?
        .getattr("modules")?
        .set_item("ardfevent_rust.routes", &routes_submodule)?;

    Ok(())
}
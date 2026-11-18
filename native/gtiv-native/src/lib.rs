use gtiv_three::{aggregate_rankings_with, GeneralOutcome, Selection, Selector};
use pyo3::exceptions::{PyOverflowError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyDict;

fn error(message: &'static str) -> PyErr {
    if message.contains("overflow") {
        PyOverflowError::new_err(message)
    } else {
        PyValueError::new_err(message)
    }
}

fn selector(value: &str) -> PyResult<Selector> {
    match value {
        "vertex" => Ok(Selector::Vertex),
        "minimum_norm" | "minimum-norm" => Ok(Selector::MinimumNorm),
        _ => Err(PyValueError::new_err(
            "selector must be 'vertex' or 'minimum_norm'",
        )),
    }
}

fn outcome_dict<'py>(py: Python<'py>, outcome: GeneralOutcome) -> PyResult<Bound<'py, PyDict>> {
    let out = PyDict::new(py);
    out.set_item("probabilities", outcome.probabilities)?;
    out.set_item("margins", outcome.margins)?;
    out.set_item(
        "exact",
        outcome
            .exact
            .iter()
            .map(|ratio| (ratio.num, ratio.den))
            .collect::<Vec<_>>(),
    )?;
    let selection = match outcome.selection {
        Selection::WeakCondorcetWinner(_) => "weak_condorcet_winner",
        Selection::SimplexVertex => "simplex_vertex",
        Selection::MinimumNorm => "minimum_norm",
    };
    out.set_item("selection", selection)?;
    if let Selection::WeakCondorcetWinner(candidate) = outcome.selection {
        out.set_item("weak_condorcet_winner", candidate)?;
    }
    let face = PyDict::new(py);
    face.set_item(
        "min",
        outcome
            .face
            .min
            .iter()
            .map(|ratio| (ratio.num, ratio.den))
            .collect::<Vec<_>>(),
    )?;
    face.set_item(
        "max",
        outcome
            .face
            .max
            .iter()
            .map(|ratio| (ratio.num, ratio.den))
            .collect::<Vec<_>>(),
    )?;
    face.set_item("nonunique", outcome.face.nonunique)?;
    out.set_item("face", face)?;
    Ok(out)
}

/// Aggregate complete rankings with the exact GT solver.
#[pyfunction(signature = (ballots, candidates, selector = "vertex"))]
fn aggregate_rankings(
    py: Python<'_>,
    ballots: Vec<Vec<usize>>,
    candidates: usize,
    selector: &str,
) -> PyResult<Py<PyDict>> {
    let selector = self::selector(selector)?;
    let result = py
        .detach(move || aggregate_rankings_with(&ballots, candidates, selector))
        .map_err(error)?;
    Ok(outcome_dict(py, result)?.unbind())
}

#[pymodule]
fn gtiv_native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add("MAX_CANDIDATES", gtiv_three::MAX_CANDIDATES)?;
    module.add("BACKEND_API_VERSION", 1)?;
    module.add("SOURCE_FINGERPRINT_SCHEMA", 1)?;
    module.add("SOURCE_SHA256", env!("GTIV_NATIVE_SOURCE_SHA256"))?;
    module.add_function(wrap_pyfunction!(aggregate_rankings, module)?)?;
    Ok(())
}

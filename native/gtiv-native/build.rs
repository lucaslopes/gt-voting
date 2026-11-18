//! Embed a stable digest of the native source files that define this module.
use sha2::{Digest, Sha256};
use std::{env, fs, path::Path};

fn main() {
    // Schema 1 frames every relative name and file length, so the digest is
    // independent of checkout path and unambiguous for different boundaries.
    let root = env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR");
    let root = Path::new(&root);
    let files = [
        ("gtiv-three/src/lib.rs", "../gtiv-three/src/lib.rs"),
        ("gtiv-three/src/general.rs", "../gtiv-three/src/general.rs"),
        ("gtiv-native/src/lib.rs", "src/lib.rs"),
        ("gtiv-native/build.rs", "build.rs"),
        ("gtiv-native/Cargo.lock", "Cargo.lock"),
    ];
    let mut digest = Sha256::new();
    digest.update(b"GTIV_NATIVE_SOURCE_V1\0");
    for (name, path) in files {
        let path = root.join(path);
        println!("cargo:rerun-if-changed={}", path.display());
        let content = fs::read(&path).unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        digest.update((name.len() as u64).to_be_bytes());
        digest.update(name.as_bytes());
        digest.update((content.len() as u64).to_be_bytes());
        digest.update(content);
    }
    println!(
        "cargo:rustc-env=GTIV_NATIVE_SOURCE_SHA256={:x}",
        digest.finalize()
    );
}

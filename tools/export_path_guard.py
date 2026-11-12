"""Preflight privacy boundary for offline public catalogue export."""
from pathlib import Path

def validate_export_paths(source, manifest, attestation, destination, receipt):
    source, manifest, attestation, destination, receipt = map(
        lambda value: Path(value).absolute(), (source, manifest, attestation, destination, receipt))
    private_inputs = (source, manifest, attestation)
    if destination.name != "public-catalogue.json":
        raise ValueError("Public export must target public-catalogue.json")
    if receipt.name == "public-catalogue.json":
        raise ValueError("Receipt cannot be named public-catalogue.json")
    if len(set(private_inputs)) != len(private_inputs):
        raise ValueError("Private editorial inputs must be distinct")
    if len({source, manifest, attestation, destination, receipt}) != 5:
        raise ValueError("Private inputs and outputs must be distinct")
    if receipt.parent == destination.parent:
        raise ValueError("Private receipt cannot share public catalogue directory")
    for path in (destination, receipt):
        if path.exists() or path.is_symlink():
            raise ValueError("Export outputs must be new files")
        if not path.parent.is_dir() or path.parent.is_symlink():
            raise ValueError("Export parent must be an existing real directory")
    for path in private_inputs:
        if path.parent == destination.parent:
            raise ValueError("Private editorial inputs cannot share public catalogue directory")
    return True

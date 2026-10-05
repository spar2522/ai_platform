#!/usr/bin/env python3
"""Compare hand-crafted reference benchmark extractor against autonomous AI-synthesized extractor."""

import importlib.util
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "packages" / "aip-canonica" / "src"))

from aip_canonica.extractors.bank.axis_bank import AxisBankStatementExtractor as SynthesizedExtractor  # noqa: E402
from aip_canonica.parsers.excel_parser import ExcelParser  # noqa: E402
from aip_canonica.parsers.pdf_parser import PdfParser  # noqa: E402
from aip_canonica.validation.validator import BankStatementValidator  # noqa: E402

# Import benchmark extractor
benchmark_path = repo_root / "packages" / "aip-canonica" / "tests" / "benchmarks" / "reference_axis.py"

spec = importlib.util.spec_from_file_location("reference_axis", benchmark_path)
ref_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref_mod)
BenchmarkExtractor = ref_mod.AxisBankStatementExtractor


def compare():
    """Compare benchmark and synthesized extractors on real-world documents."""
    # Initialize components
    benchmark_extractor = BenchmarkExtractor()
    synthesized_extractor = SynthesizedExtractor()
    validator = BankStatementValidator()

    # File paths (hardcoded for demonstration - consider external configuration for production)
    pdf_path = Path("/Users/arpitratan/Downloads/Axis Statement.pdf")
    xls_path = Path("/Users/arpitratan/Desktop/IT returns 2025-2026/Axis SB Statement.xls")

    print("=" * 80)
    print(" GROUND TRUTH VALIDATION: BENCHMARK vs AUTONOMOUS AI-SYNTHESIZED EXTRACTOR")
    print("=" * 80)

    # Process each document type
    for file_path, file_type in [(pdf_path, "PDF - MULTILINE LAYOUT"), (xls_path, "XLS - TABULAR LAYOUT")]:
        try:
            # Parse document
            parser = PdfParser() if file_path.suffix.lower() == ".pdf" else ExcelParser()
            parsed_doc = parser.parse(file_path)
            
            # Extract data
            benchmark_doc = benchmark_extractor.extract(parsed_doc)
            synthesized_doc = synthesized_extractor.extract(parsed_doc)
            
            # Validate results
            benchmark_valid = validator.validate(benchmark_doc)
            synthesized_valid = validator.validate(synthesized_doc)
            
            # Display results
            print(f"\n--- {file_type} ---")
            print(f"{'Metric':<30} | {'Benchmark (Handcrafted)':<22} | {'Synthesized (AI-Learned)':<22} | {'Match?'}")
            print("-" * 85)
            
            metrics = [
                ("Matches() Detection", benchmark_extractor.matches(parsed_doc), synthesized_extractor.matches(parsed_doc)),
                ("Account Number", benchmark_doc.account_number, synthesized_doc.account_number),
                ("Holder Name", benchmark_doc.holder.name if benchmark_doc.holder else "N/A", synthesized_doc.holder.name if synthesized_doc.holder else "N/A"),
                ("Opening Balance", str(benchmark_doc.opening_balance), str(synthesized_doc.opening_balance)),
                ("Closing Balance", str(benchmark_doc.closing_balance), str(synthesized_doc.closing_balance)),
                ("Transactions Extracted", len(benchmark_doc.transactions), len(synthesized_doc.transactions)),
                ("Validation Passed", benchmark_valid.is_valid, synthesized_valid.is_valid),
                ("Discrepancy", benchmark_valid.metrics.get("discrepancy"), synthesized_valid.metrics.get("discrepancy")),
            ]
            
            for name, b_val, s_val in metrics:
                match_str = "✔ IDENTICAL" if str(b_val) == str(s_val) else f"DIFF ({b_val} vs {s_val})"
                print(f"{name:<30} | {str(b_val):<22} | {str(s_val):<22} | {match_str}")
            
        except Exception as e:
            print(f"\nError processing {file_type}: {str(e)}")


if __name__ == "__main__":
    compare()
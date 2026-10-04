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
    bench = BenchmarkExtractor()
    synth = SynthesizedExtractor()
    val = BankStatementValidator()

    pdf_path = Path("/Users/arpitratan/Downloads/Axis Statement.pdf")
    xls_path = Path("/Users/arpitratan/Desktop/IT returns 2025-2026/Axis SB Statement.xls")

    print("=" * 80)
    print(" GROUND TRUTH VALIDATION: BENCHMARK vs AUTONOMOUS AI-SYNTHESIZED EXTRACTOR")
    print("=" * 80)

    # 1. Compare on PDF
    if pdf_path.exists():
        pdf_wb = PdfParser().parse(pdf_path)
        doc_bench_pdf = bench.extract(pdf_wb)
        doc_synth_pdf = synth.extract(pdf_wb)
        val_bench_pdf = val.validate(doc_bench_pdf)
        val_synth_pdf = val.validate(doc_synth_pdf)

        print("\n--- 1. AXIS STATEMENT (PDF - MULTILINE LAYOUT) ---")
        print(f"{'Metric':<30} | {'Benchmark (Handcrafted)':<22} | {'Synthesized (AI-Learned)':<22} | {'Match?'}")
        print("-" * 85)
        metrics = [
            ("Matches() Detection", bench.matches(pdf_wb), synth.matches(pdf_wb)),
            ("Account Number", doc_bench_pdf.account_number, doc_synth_pdf.account_number),
            ("Holder Name", doc_bench_pdf.holder.name if doc_bench_pdf.holder else "N/A", doc_synth_pdf.holder.name if doc_synth_pdf.holder else "N/A"),
            ("Opening Balance", str(doc_bench_pdf.opening_balance), str(doc_synth_pdf.opening_balance)),
            ("Closing Balance", str(doc_bench_pdf.closing_balance), str(doc_synth_pdf.closing_balance)),
            ("Transactions Extracted", len(doc_bench_pdf.transactions), len(doc_synth_pdf.transactions)),
            ("Validation Passed", val_bench_pdf.is_valid, val_synth_pdf.is_valid),
            ("Discrepancy", val_bench_pdf.metrics.get("discrepancy"), val_synth_pdf.metrics.get("discrepancy")),
        ]
        for name, b_val, s_val in metrics:
            match_str = "✔ IDENTICAL" if str(b_val) == str(s_val) else f"DIFF ({b_val} vs {s_val})"
            print(f"{name:<30} | {str(b_val):<22} | {str(s_val):<22} | {match_str}")

    # 2. Compare on XLS
    if xls_path.exists():
        xls_wb = ExcelParser().parse(xls_path)
        doc_bench_xls = bench.extract(xls_wb)
        doc_synth_xls = synth.extract(xls_wb)
        val_bench_xls = val.validate(doc_bench_xls)
        val_synth_xls = val.validate(doc_synth_xls)

        print("\n--- 2. AXIS STATEMENT (XLS - TABULAR LAYOUT) ---")
        print(f"{'Metric':<30} | {'Benchmark (Handcrafted)':<22} | {'Synthesized (AI-Learned)':<22} | {'Match?'}")
        print("-" * 85)
        metrics_xls = [
            ("Matches() Detection", bench.matches(xls_wb), synth.matches(xls_wb)),
            ("Account Number", doc_bench_xls.account_number, doc_synth_xls.account_number),
            ("Holder Name", doc_bench_xls.holder.name if doc_bench_xls.holder else "N/A", doc_synth_xls.holder.name if doc_synth_xls.holder else "N/A"),
            ("Opening Balance", str(doc_bench_xls.opening_balance), str(doc_synth_xls.opening_balance)),
            ("Closing Balance", str(doc_bench_xls.closing_balance), str(doc_synth_xls.closing_balance)),
            ("Transactions Extracted", len(doc_bench_xls.transactions), len(doc_synth_xls.transactions)),
            ("Validation Passed", val_bench_xls.is_valid, val_synth_xls.is_valid),
            ("Discrepancy", val_bench_xls.metrics.get("discrepancy"), val_synth_xls.metrics.get("discrepancy")),
        ]
        for name, b_val, s_val in metrics_xls:
            match_str = "✔ IDENTICAL" if str(b_val) == str(s_val) else f"DIFF ({b_val} vs {s_val})"
            print(f"{name:<30} | {str(b_val):<22} | {str(s_val):<22} | {match_str}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    compare()

<answer>
The provided Python code is part of a document verification and data extraction system, likely used to analyze and process structured documents (e.g., Excel files, bank statements, invoices) by leveraging AI and deterministic parsing strategies. Here's a breakdown of its key components and functionality:

1. **Document Preview & Analysis**:
   - Displays a preview of the first few rows of a document's sheet, showing cell values and metadata (e.g., row index, number of cells).
   - Determines if the document contains vector text (digital text vs. scanned raster images) and recommends AI-based strategies for extraction (e.g., OCR fallback or learning-based extractors).

2. **Custom File Verification**:
   - The `verify_custom_file` function processes a user-supplied file, using AI (Gemini or local model) if enabled.
   - Validates the extracted data, outputs document type, metadata (e.g., AI audit details), and sample content (e.g., bank transactions, invoice line items).
   - Supports promoting learned extractors to production if enabled via the `--promote` flag.

3. **AI Integration**:
   - Uses AI for OCR fallback (when text is rasterized) and strategy learning (to synthesize specialized extractors for complex layouts).
   - Handles both deterministic (no AI) and AI-enhanced modes, with network usage tracking (e.g., "EXTERNAL INTERNET" vs. "LOCALHOST ONLY").

4. **Command-Line Interface**:
   - Accepts arguments like `--ai`, `--file`, `--learn`, `--promote`, and `--debug` to control behavior.
   - Runs a deterministic test suite by default, with AI-based tests optional.

5. **Document-Specific Output**:
   - Tailors output based on document type (e.g., BankStatement, Invoice, Ledger), showing relevant metadata (e.g., account numbers, transaction samples).

**Usage Example**:  
To verify a custom Excel file with AI:  
```bash
python script.py --file path/to/document.xlsx --ai --promote
```  
This would analyze the file, use AI for extraction, and attempt to promote any learned extractors to production.

The code emphasizes flexibility, validation, and integration of AI for handling diverse document formats and layouts.
</answer>
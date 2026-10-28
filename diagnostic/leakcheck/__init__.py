"""leakcheck: look-ahead leakage diagnostics for LLM-coded text measures."""

from diagnostic.leakcheck.core import LeakageResult, auc_table, estimate, verdict

__all__ = ["LeakageResult", "auc_table", "estimate", "verdict"]

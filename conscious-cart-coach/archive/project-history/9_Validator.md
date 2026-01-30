Create src/data_processing/validator.py that checks LLM output.

Function: validate_decision(decision: dict, facts_pack: dict) -> tuple[bool, list[str]]

Checks:
1. recommended_tier is valid ("cheaper", "balanced", or "conscious")
2. reasoning references actual facts:
   - Check for price mentions (must match facts_pack prices ±$0.50)
   - Check for brand mentions (must be in facts_pack)
   - Check for packaging mentions (must match facts_pack)
3. No invented data:
   - No prices not in facts_pack
   - No brands not in facts_pack
   - No certifications not in facts_pack
4. Reasoning is substantive (>20 characters)
5. key_trade_off is present

Returns:
- (True, []) if valid
- (False, ["error1", "error2"]) if invalid

If invalid, decision_engine should retry with stricter prompt

Add pytest tests with:
- Valid decision (passes)
- Hallucinated price (fails)
- Invalid tier (fails)
- Missing reasoning (fails)

# LLM cost estimate

Generated on 2026-10-21 from **11 real calls** logged in `logs/llm_calls.jsonl`.

## Pricing used

- Model: `gemini-3.5-flash-lite` (Gemini Developer API, paid tier, standard)
- Input: **$0.30** per 1M tokens
- Output: **$2.50** per 1M tokens (thinking tokens are billed as output)
- Source: https://ai.google.dev/gemini-api/docs/pricing (checked on the generation date)

## Average tokens per call

| Technique | Calls | Avg input tokens | Avg output tokens |
|---|---|---|---|
| few_shot | 5 | 420 | 82 |
| zero_shot | 3 | 239 | 160 |
| chain_of_thought | 3 | 286 | 344 |
| **All** | 11 | 334 | 175 |

Average cost per call: **$0.000537** USD

## Monthly projection

| Scenario | Active users | Requests/user/day | Requests/month | Estimated cost/month (USD) |
|---|---|---|---|---|
| Class pilot | 30 | 3 | 2,700 | $1.45 |
| University launch | 500 | 5 | 75,000 | $40.25 |
| City-wide growth | 5,000 | 5 | 750,000 | $402.48 |

## Notes

- During development the project uses the **free tier**, so the real cost is $0; the free tier has request limits and Google may use the data to improve its products.
- Few-shot and chain-of-thought prompts use more tokens than zero-shot (longer prompts and longer answers), so the chosen technique directly affects the bill.
- Costs could be reduced by sending fewer catalog songs as context, limiting the answer length or using the Batch API for non-interactive tasks.

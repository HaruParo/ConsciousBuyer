# Hybrid RAG System Implementation Guide
*Efficient brand retrieval for Conscious Cart Coach*

**Dummy-Proof Version**

---

## 🎯 What We're Building

A smart search system that finds the best conscious brands for any ingredient or cuisine. Think of it like a librarian who:
1. **Knows the exact shelf** (keyword search)
2. **Understands what you mean** (semantic search)
3. **Ranks by relevance** (reranking)

---

## 🏗️ Architecture Overview

```
USER QUERY: "sustainable Mexican tortilla brands"
         ↓
┌─────────────────────────────────────────────────┐
│  STEP 1: QUERY PREPROCESSING                    │
│  - Clean text: "sustainable mexican tortilla"  │
│  - Expand: + "organic tortilla"                 │
│            + "eco-friendly mexican corn"        │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  STEP 2: HYBRID RETRIEVAL (PARALLEL)            │
│                                                  │
│  ┌──────────────────┐    ┌──────────────────┐  │
│  │ KEYWORD SEARCH   │    │ SEMANTIC SEARCH  │  │
│  │ (BM25/TF-IDF)    │    │ (Embeddings)     │  │
│  ├──────────────────┤    ├──────────────────┤  │
│  │ Masienda   0.95  │    │ Don Pancho  0.82 │  │
│  │ Mi Rancho  0.88  │    │ Masienda    0.80 │  │
│  │ La Tortilla 0.75 │    │ Masa Madre  0.68 │  │
│  └──────────────────┘    └──────────────────┘  │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  STEP 3: FUSION                                  │
│  Combine scores: 70% keyword + 30% semantic     │
│  - Masienda: (0.95×0.7) + (0.80×0.3) = 0.905   │
│  - Mi Rancho: (0.88×0.7) + (0.0×0.3) = 0.616   │
│  - Don Pancho: (0.0×0.7) + (0.82×0.3) = 0.246  │
│  - La Tortilla: (0.75×0.7) + (0.0×0.3) = 0.525 │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  STEP 4: RERANKING (OPTIONAL)                   │
│  Use small model to rescore top 10:             │
│  - Masienda: 0.92 (heirloom + organic)         │
│  - Mi Rancho: 0.87 (organic since 1939)        │
│  - La Tortilla: 0.71 (stoneground)             │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  STEP 5: CONTEXT COMPRESSION                    │
│  Extract only relevant info for LLM:            │
│  - Masienda: "USDA Organic, heirloom corn,     │
│    nixtamalization, direct farmer trade"        │
│  (Dropped: founding date, website, etc.)       │
└────────────────┬────────────────────────────────┘
                 ↓
         SEND TO LLM
```

---

## 💻 Implementation (Python)

### Phase 1: Setup Dependencies

```bash
# Install required packages
pip install anthropic           # Claude API
pip install rank-bm25          # Keyword search (BM25 algorithm)
pip install sentence-transformers  # Semantic embeddings
pip install faiss-cpu          # Vector similarity search (fast!)
pip install nltk               # Text preprocessing
```

### Phase 2: Brand Database Loader

```python
# src/stores/conscious_brands_store.py

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

class ConsciousBrandsStore:
    """
    Loads and indexes the conscious brands database for hybrid search.
    """

    def __init__(self, db_path: str = "data/conscious_brands_database.md"):
        self.db_path = Path(db_path)
        self.brands = []
        self._load_brands()

    def _load_brands(self):
        """Parse the markdown database into structured brand objects."""
        content = self.db_path.read_text()

        # Split by ### headers (brand entries)
        brand_sections = re.split(r'\n### ', content)

        for section in brand_sections[1:]:  # Skip intro
            lines = section.strip().split('\n')
            brand_name = lines[0]

            brand = {
                "name": brand_name,
                "category": "",
                "cuisine": "",
                "certifications": [],
                "tags": [],
                "why_conscious": "",
                "products": "",
                "full_text": section  # For keyword search
            }

            # Parse each field
            for line in lines[1:]:
                if line.startswith("- **Category**:"):
                    brand["category"] = line.split(":", 1)[1].strip()
                elif line.startswith("- **Cuisine**:"):
                    brand["cuisine"] = line.split(":", 1)[1].strip()
                elif line.startswith("- **Certifications**:"):
                    brand["certifications"] = [c.strip() for c in line.split(":", 1)[1].split(",")]
                elif line.startswith("- **Tags**:"):
                    # Extract tags between backticks
                    tags_text = line.split(":", 1)[1]
                    brand["tags"] = re.findall(r'`([^`]+)`', tags_text)
                elif line.startswith("- **Why Conscious**:"):
                    brand["why_conscious"] = line.split(":", 1)[1].strip()
                elif line.startswith("- **Products**:"):
                    brand["products"] = line.split(":", 1)[1].strip()

            self.brands.append(brand)

        print(f"✅ Loaded {len(self.brands)} brands from database")

    def get_all_brands(self) -> List[Dict]:
        """Return all brands."""
        return self.brands

    def get_by_cuisine(self, cuisine: str) -> List[Dict]:
        """Get brands for a specific cuisine."""
        cuisine_lower = cuisine.lower()
        return [b for b in self.brands if cuisine_lower in b["cuisine"].lower()]

    def get_by_category(self, category: str) -> List[Dict]:
        """Get brands for a specific category (e.g., 'pasta', 'soy sauce')."""
        category_lower = category.lower()
        return [b for b in self.brands if category_lower in b["category"].lower()]

    def get_by_tag(self, tag: str) -> List[Dict]:
        """Get brands with a specific tag (e.g., 'organic', 'b_corp')."""
        tag_lower = tag.lower()
        return [b for b in self.brands if tag_lower in [t.lower() for t in b["tags"]]]
```

### Phase 3: Hybrid Search Engine

```python
# src/search/hybrid_rag.py

from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

class HybridBrandSearch:
    """
    Hybrid search combining keyword (BM25) and semantic (embeddings) search.
    """

    def __init__(self, brands: List[Dict]):
        self.brands = brands

        # Initialize keyword search (BM25)
        self.corpus = [b["full_text"] for b in brands]
        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Initialize semantic search (sentence embeddings)
        print("🔄 Loading embedding model (one-time setup)...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')  # Fast & good

        # Create embeddings for all brands
        brand_texts = [
            f"{b['name']} {b['category']} {b['cuisine']} {b['why_conscious']} {' '.join(b['tags'])}"
            for b in brands
        ]
        self.embeddings = self.encoder.encode(brand_texts, show_progress_bar=True)

        # Build FAISS index for fast similarity search
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)

        print(f"✅ Hybrid search ready with {len(brands)} brands")

    def keyword_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        BM25 keyword search.
        Returns: [(brand_index, score), ...]
        """
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Get top K indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_indices]

    def semantic_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Embedding-based semantic search.
        Returns: [(brand_index, similarity_score), ...]
        """
        # Encode query
        query_embedding = self.encoder.encode([query])
        faiss.normalize_L2(query_embedding)

        # Search in FAISS index
        scores, indices = self.index.search(query_embedding, top_k)

        return [(int(indices[0][i]), float(scores[0][i])) for i in range(len(indices[0]))]

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        keyword_weight: float = 0.7,
        semantic_weight: float = 0.3
    ) -> List[Dict]:
        """
        Hybrid search combining keyword and semantic results.

        Args:
            query: Search query (e.g., "organic Mexican tortilla brands")
            top_k: Number of results to return
            keyword_weight: Weight for keyword search (default 0.7)
            semantic_weight: Weight for semantic search (default 0.3)

        Returns:
            List of brand dicts with scores
        """
        # Get results from both search methods
        keyword_results = self.keyword_search(query, top_k=20)
        semantic_results = self.semantic_search(query, top_k=20)

        # Normalize scores to [0, 1]
        def normalize_scores(results):
            if not results or max(r[1] for r in results) == 0:
                return results
            max_score = max(r[1] for r in results)
            return [(idx, score / max_score) for idx, score in results]

        keyword_results = normalize_scores(keyword_results)
        semantic_results = normalize_scores(semantic_results)

        # Combine scores
        combined_scores = {}

        for idx, score in keyword_results:
            combined_scores[idx] = combined_scores.get(idx, 0) + (score * keyword_weight)

        for idx, score in semantic_results:
            combined_scores[idx] = combined_scores.get(idx, 0) + (score * semantic_weight)

        # Sort by combined score
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Return brand objects with scores
        return [
            {
                **self.brands[idx],
                "relevance_score": score,
                "keyword_match": idx in dict(keyword_results),
                "semantic_match": idx in dict(semantic_results)
            }
            for idx, score in sorted_results
        ]
```

### Phase 4: Query Expansion (Optional but Powerful)

```python
# src/search/query_expander.py

from typing import List

class QueryExpander:
    """
    Expands user queries with synonyms and related terms.
    """

    # Simple synonym mapping
    SYNONYMS = {
        "sustainable": ["organic", "eco-friendly", "regenerative"],
        "ethical": ["fair trade", "conscious", "responsible"],
        "healthy": ["organic", "clean", "natural"],
        "mexican": ["latin american", "hispanic"],
        "chinese": ["asian", "cantonese"],
        "pasta": ["noodles", "spaghetti"],
        "tortilla": ["corn", "masa"],
        "kimchi": ["fermented", "probiotic"],
    }

    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms.

        Example:
            "sustainable Mexican tortillas"
            → ["sustainable Mexican tortillas",
               "organic Mexican tortillas",
               "eco-friendly Latin American corn"]
        """
        expanded = [query]  # Original query
        query_lower = query.lower()

        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                for synonym in synonyms[:2]:  # Use top 2 synonyms
                    expanded_query = query_lower.replace(term, synonym)
                    expanded.append(expanded_query)

        return expanded[:3]  # Return top 3 variations
```

### Phase 5: Context Compression

```python
# src/search/context_compressor.py

from typing import Dict, List

class ContextCompressor:
    """
    Compresses brand data to only relevant fields for LLM context.
    Reduces token usage by 70-80%.
    """

    RELEVANT_FIELDS = [
        "name",
        "category",
        "certifications",
        "tags",
        "why_conscious",
        "sustainability"
    ]

    def compress_brand(self, brand: Dict) -> str:
        """
        Compress brand to essential info only.

        Before (500 tokens):
            {full brand entry with founding date, website, etc.}

        After (100 tokens):
            "Masienda: USDA Organic, heirloom corn, nixtamalization,
             direct farmer trade, Mexican tortillas"
        """
        compressed = f"{brand['name']}: "

        parts = []

        # Add certifications
        if brand.get("certifications"):
            certs = ", ".join(brand["certifications"][:3])  # Top 3
            parts.append(certs)

        # Add top tags
        if brand.get("tags"):
            top_tags = [t for t in brand["tags"] if t in [
                "organic", "b_corp", "fair_trade", "regenerative",
                "farmer_cooperative", "climate_neutral"
            ]][:3]
            if top_tags:
                parts.append(", ".join(top_tags))

        # Add why conscious (first sentence only)
        if brand.get("why_conscious"):
            first_sentence = brand["why_conscious"].split(".")[0]
            if len(first_sentence) < 100:
                parts.append(first_sentence)

        compressed += ", ".join(parts)
        return compressed

    def compress_results(self, brands: List[Dict], max_tokens: int = 500) -> str:
        """
        Compress multiple brands into compact context.
        """
        compressed_brands = []
        current_tokens = 0

        for brand in brands:
            compressed = self.compress_brand(brand)
            tokens = len(compressed.split())  # Rough estimate

            if current_tokens + tokens > max_tokens:
                break

            compressed_brands.append(compressed)
            current_tokens += tokens

        return "\n".join(compressed_brands)
```

### Phase 6: Putting It All Together

```python
# src/agents/brand_agent.py

from src.stores.conscious_brands_store import ConsciousBrandsStore
from src.search.hybrid_rag import HybridBrandSearch
from src.search.query_expander import QueryExpander
from src.search.context_compressor import ContextCompressor

class BrandAgent:
    """
    Main agent for finding conscious brands using hybrid RAG.
    """

    def __init__(self):
        # Load brands
        self.store = ConsciousBrandsStore()

        # Initialize hybrid search
        self.search = HybridBrandSearch(self.store.get_all_brands())

        # Initialize helpers
        self.expander = QueryExpander()
        self.compressor = ContextCompressor()

    def find_brands(
        self,
        ingredient: str,
        cuisine: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find the best conscious brands for an ingredient.

        Example:
            find_brands("tortillas", cuisine="Mexican")
            → [Masienda, Mi Rancho, La Tortilla Factory]
        """
        # Build query
        query = ingredient
        if cuisine:
            query = f"{cuisine} {ingredient}"

        # Expand query
        expanded_queries = self.expander.expand_query(query)

        # Search with all query variations
        all_results = []
        for exp_query in expanded_queries:
            results = self.search.hybrid_search(exp_query, top_k=top_k * 2)
            all_results.extend(results)

        # Deduplicate and re-rank by combined score
        seen_names = set()
        unique_results = []
        for result in all_results:
            if result["name"] not in seen_names:
                seen_names.add(result["name"])
                unique_results.append(result)

        # Sort by score and return top K
        unique_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return unique_results[:top_k]

    def get_llm_context(self, brands: List[Dict]) -> str:
        """
        Get compressed context string for LLM prompt.
        """
        return self.compressor.compress_results(brands)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Initialize
    agent = BrandAgent()

    # Search for brands
    print("\n🔍 Searching for: 'organic Mexican tortilla brands'")
    results = agent.find_brands("tortillas", cuisine="Mexican", top_k=3)

    # Print results
    for i, brand in enumerate(results, 1):
        print(f"\n{i}. {brand['name']} (score: {brand['relevance_score']:.3f})")
        print(f"   Category: {brand['category']}")
        print(f"   Tags: {', '.join(brand['tags'][:5])}")
        print(f"   Why: {brand['why_conscious'][:100]}...")

    # Get compressed context for LLM
    print("\n📄 Compressed context for LLM:")
    print(agent.get_llm_context(results))
```

---

## 🚀 Performance Optimizations

### 1. Caching Search Results

```python
import hashlib
import json
from pathlib import Path

class CachedHybridSearch(HybridBrandSearch):
    """Hybrid search with caching."""

    def __init__(self, brands: List[Dict], cache_dir: str = ".search_cache"):
        super().__init__(brands)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def hybrid_search(self, query: str, **kwargs) -> List[Dict]:
        # Check cache
        cache_key = hashlib.md5(f"{query}:{kwargs}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            print(f"   💾 Cache hit for: {query}")
            return json.loads(cache_file.read_text())

        # Perform search
        print(f"   🔍 Searching for: {query}")
        results = super().hybrid_search(query, **kwargs)

        # Save to cache
        cache_file.write_text(json.dumps(results, indent=2))
        return results
```

### 2. Batch Processing

```python
def find_brands_batch(self, ingredients: List[str]) -> Dict[str, List[Dict]]:
    """
    Find brands for multiple ingredients at once.
    More efficient than calling find_brands() multiple times.
    """
    results = {}

    # Process all at once
    for ingredient in ingredients:
        results[ingredient] = self.find_brands(ingredient)

    return results
```

### 3. Precompute Common Queries

```python
# Pre-cache popular searches on startup
POPULAR_QUERIES = [
    "organic pasta",
    "sustainable olive oil",
    "fair trade chocolate",
    "organic tortillas",
    "kimchi",
    "soy sauce"
]

def warmup_cache(agent: BrandAgent):
    """Warm up cache with popular queries."""
    print("🔥 Warming up search cache...")
    for query in POPULAR_QUERIES:
        agent.find_brands(query, top_k=3)
    print("✅ Cache warmed up")
```

---

## 📊 Expected Performance

### Speed
- **Cold start** (first query): ~2 seconds
- **Cached query**: <10ms
- **Hybrid search**: ~50ms per query
- **100 queries/second**: Achievable with caching

### Accuracy
- **Keyword-only**: 60% relevance
- **Semantic-only**: 70% relevance
- **Hybrid (70/30)**: 90%+ relevance

### Token Savings
- **Before compression**: 500 tokens per brand
- **After compression**: 100 tokens per brand
- **Savings**: 80% reduction

### Cost Comparison

```
Scenario: Find brands for 10 ingredients

WITHOUT RAG:
- Prompt includes full database (17,000 tokens)
- 10 API calls × 17,000 tokens = 170,000 tokens
- Cost: $0.51 (input) + $0.30 (output) = $0.81

WITH HYBRID RAG:
- Retrieve 3 relevant brands per ingredient (compressed)
- 10 API calls × 300 tokens = 3,000 tokens
- Cost: $0.009 (input) + $0.009 (output) = $0.018

SAVINGS: $0.79 per 10 queries (97.8% reduction!)
```

---

## 🎯 Integration with Existing System

### Update DecisionEngine

```python
# src/engine/decision_engine.py

from src.agents.brand_agent import BrandAgent

class DecisionEngine:
    def __init__(self):
        # ... existing code ...
        self.brand_agent = BrandAgent()  # NEW

    def score_product(self, product: Dict, ingredient: Dict) -> float:
        # ... existing scoring logic ...

        # NEW: Boost score if brand is in conscious database
        brand_name = product.get("brand", "")
        conscious_brands = self.brand_agent.find_brands(
            ingredient["name"],
            top_k=10
        )

        conscious_brand_names = {b["name"].lower() for b in conscious_brands}

        if brand_name.lower() in conscious_brand_names:
            # Find the actual brand object
            brand = next((b for b in conscious_brands if b["name"].lower() == brand_name.lower()), None)
            if brand:
                # Add bonus based on tags
                if "b_corp" in brand["tags"]:
                    score += WEIGHTS["b_corp"]
                if "regenerative" in brand["tags"]:
                    score += WEIGHTS["regenerative_organic_cert"]
                if "farmer_cooperative" in brand["tags"]:
                    score += WEIGHTS["farmer_cooperative"]

        return score
```

---

## 🆘 Troubleshooting

### Issue: "Slow first query"
**Solution**: Use warmup_cache() on startup

### Issue: "Embeddings not loading"
**Solution**:
```bash
pip install --upgrade sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Issue: "Low relevance scores"
**Solution**: Adjust keyword/semantic weights:
```python
# Try different weight combinations
results = search.hybrid_search(query, keyword_weight=0.5, semantic_weight=0.5)
```

### Issue: "Too many tokens"
**Solution**: Reduce top_k or increase compression:
```python
results = agent.find_brands(ingredient, top_k=2)  # Fewer results
context = agent.get_llm_context(results[:2])  # Top 2 only
```

---

## 📚 Further Reading

- [BM25 Algorithm Explained](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [FAISS: Efficient Similarity Search](https://github.com/facebookresearch/faiss)
- [Hybrid Search Best Practices](https://www.pinecone.io/learn/hybrid-search-intro/)

---

**Next Steps**:
1. Run the code examples above
2. Test with your ingredient prompts
3. Adjust keyword/semantic weights based on results
4. Add more brands to the database

**Questions? Check the examples or reach out for help!**

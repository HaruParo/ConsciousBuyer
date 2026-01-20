"""
Tests for the Open Food Facts API client.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.data_processing.open_food_facts import (
    get_product_by_barcode,
    search_products,
    search_by_category,
    get_off_alternatives_for_category,
    _normalize_product,
    _parse_packaging,
    _organize_into_tiers,
    _format_as_alternative,
    CATEGORY_TO_OFF_TAG,
)


# Mock API response data
@pytest.fixture
def mock_product_response():
    """Mock response for a single product lookup."""
    return {
        "status": 1,
        "product": {
            "code": "3017620422003",
            "product_name": "Nutella",
            "brands": "Ferrero",
            "categories_tags": ["en:spreads", "en:sweet-spreads", "en:hazelnut-spreads"],
            "nutrition_grades": "e",
            "nova_group": 4,
            "ecoscore_grade": "d",
            "packaging": "glass jar, plastic lid",
            "labels_tags": ["en:no-palm-oil"],
            "nutriments": {
                "energy-kcal_100g": 539,
                "fat_100g": 30.9,
                "saturated-fat_100g": 10.6,
                "carbohydrates_100g": 57.5,
                "sugars_100g": 56.3,
                "fiber_100g": 0,
                "proteins_100g": 6.3,
                "salt_100g": 0.107,
            },
        },
    }


@pytest.fixture
def mock_search_response():
    """Mock response for a search query."""
    return {
        "count": 3,
        "products": [
            {
                "code": "123456789",
                "product_name": "Organic Whole Milk",
                "brands": "Happy Farms",
                "categories_tags": ["en:milks", "en:organic-milks"],
                "nutrition_grades": "a",
                "nova_group": 1,
                "ecoscore_grade": "b",
                "labels_tags": ["en:organic", "en:usda-organic"],
                "nutriments": {"proteins_100g": 3.2, "fat_100g": 3.5},
            },
            {
                "code": "987654321",
                "product_name": "2% Reduced Fat Milk",
                "brands": "Store Brand",
                "categories_tags": ["en:milks"],
                "nutrition_grades": "b",
                "nova_group": 1,
                "ecoscore_grade": "c",
                "labels_tags": [],
                "nutriments": {"proteins_100g": 3.3, "fat_100g": 2.0},
            },
            {
                "code": "111222333",
                "product_name": "Chocolate Milk",
                "brands": "Nesquik",
                "categories_tags": ["en:milks", "en:chocolate-milks"],
                "nutrition_grades": "d",
                "nova_group": 4,
                "ecoscore_grade": "d",
                "labels_tags": [],
                "nutriments": {"proteins_100g": 3.0, "fat_100g": 1.5, "sugars_100g": 10.0},
            },
        ],
    }


class TestParsePackaging:
    """Tests for packaging data parsing."""

    def test_parse_structured_packaging(self):
        """Test parsing structured packagings array."""
        product = {
            "packagings": [
                {
                    "shape": "en:bottle",
                    "material": "en:glass",
                    "recycling": "en:recycle",
                    "number_of_units": 1,
                },
                {
                    "shape": "en:lid",
                    "material": "en:metal",
                    "recycling": "en:recycle",
                },
            ],
            "packaging": "glass bottle, metal lid",
        }
        result = _parse_packaging(product)

        assert len(result["components"]) == 2
        assert "glass" in result["materials"]
        assert "metal" in result["materials"]
        assert result["recyclable_ratio"] == 1.0
        assert result["packaging_rating"] == "good"

    def test_parse_plastic_packaging(self):
        """Test parsing plastic packaging gets poor rating."""
        product = {
            "packagings": [
                {
                    "material": "en:plastic",
                    "recycling": "en:discard",
                }
            ],
        }
        result = _parse_packaging(product)

        assert "plastic" in result["materials"]
        assert result["packaging_rating"] == "poor"
        assert result["recyclable_ratio"] == 0.0

    def test_parse_mixed_packaging(self):
        """Test parsing mixed materials."""
        product = {
            "packagings": [
                {"material": "en:glass"},
                {"material": "en:plastic"},
            ],
        }
        result = _parse_packaging(product)

        assert result["packaging_rating"] == "mixed"

    def test_parse_empty_packaging(self):
        """Test parsing empty packaging data."""
        result = _parse_packaging({})

        assert result["components"] == []
        assert result["materials"] == []
        assert result["packaging_rating"] == "unknown"
        assert result["recyclable_ratio"] is None

    def test_parse_packaging_tags(self):
        """Test parsing packaging tags."""
        product = {
            "packaging_tags": ["en:glass", "en:bottle", "en:recyclable-materials"],
        }
        result = _parse_packaging(product)

        assert "glass" in result["tags"]
        assert "bottle" in result["tags"]


class TestNormalizeProduct:
    """Tests for product normalization."""

    def test_normalize_full_product(self, mock_product_response):
        """Test normalizing a product with all fields."""
        product = mock_product_response["product"]
        normalized = _normalize_product(product)

        assert normalized["barcode"] == "3017620422003"
        assert normalized["product_name"] == "Nutella"
        assert normalized["brand"] == "Ferrero"
        assert normalized["nutrition_grade"] == "e"
        assert normalized["nova_group"] == 4
        assert normalized["ecoscore"] == "d"
        assert "No Palm Oil" in normalized["certifications"]
        assert normalized["source"] == "open_food_facts"
        assert "packaging_details" in normalized

    def test_normalize_nutrition_data(self, mock_product_response):
        """Test that nutrition data is properly extracted."""
        product = mock_product_response["product"]
        normalized = _normalize_product(product)

        assert normalized["nutrition"]["energy_kcal_100g"] == 539
        assert normalized["nutrition"]["fat_100g"] == 30.9
        assert normalized["nutrition"]["sugars_100g"] == 56.3
        assert normalized["nutrition"]["proteins_100g"] == 6.3

    def test_normalize_empty_product(self):
        """Test normalizing an empty product."""
        normalized = _normalize_product({})

        assert normalized["product_name"] == "Unknown"
        assert normalized["brand"] == "Unknown"
        assert normalized["certifications"] == []
        assert normalized["nutrition"] == {}

    def test_normalize_categories(self):
        """Test that categories are cleaned up."""
        product = {
            "categories_tags": ["en:dairy", "en:organic-milks", "en:whole-milks"]
        }
        normalized = _normalize_product(product)

        assert "dairy" in normalized["categories"]
        assert "organic milks" in normalized["categories"]


class TestOrganizeIntoTiers:
    """Tests for organizing products into tiers."""

    def test_organize_creates_all_tiers(self, mock_search_response):
        """Test that all three tiers are created."""
        products = [_normalize_product(p) for p in mock_search_response["products"]]
        tiers = _organize_into_tiers(products)

        assert "conscious" in tiers
        assert "balanced" in tiers
        assert "cheaper" in tiers

    def test_conscious_tier_prefers_organic(self, mock_search_response):
        """Test that conscious tier prefers organic products."""
        products = [_normalize_product(p) for p in mock_search_response["products"]]
        tiers = _organize_into_tiers(products)

        # The organic milk should be in conscious tier
        assert "Organic" in tiers["conscious"]["certifications"] or \
               tiers["conscious"]["ecoscore"] in ("a", "b")

    def test_organize_empty_list(self):
        """Test organizing an empty product list."""
        tiers = _organize_into_tiers([])
        assert tiers is None


class TestFormatAsAlternative:
    """Tests for formatting products as alternatives."""

    def test_format_conscious_tier(self):
        """Test formatting a product for conscious tier."""
        product = {
            "barcode": "123",
            "product_name": "Organic Miso",
            "brand": "Eden",
            "certifications": ["Organic", "Non Gmo"],
            "nutrition_grade": "a",
            "ecoscore": "b",
            "nova_group": 1,
            "packaging": "glass jar",
            "nutrition": {"proteins_100g": 12},
        }
        alt = _format_as_alternative(product, "conscious")

        assert alt["brand"] == "Eden"
        assert alt["product_name"] == "Organic Miso"
        assert "Organic certified" in alt["why_this_tier"]
        assert alt["source"] == "open_food_facts"
        assert "openfoodfacts.org/product/123" in alt["source_url"]

    def test_format_cheaper_tier(self):
        """Test formatting a product for cheaper tier."""
        product = {
            "barcode": "456",
            "product_name": "Basic Yogurt",
            "brand": "Store Brand",
            "certifications": [],
            "nutrition_grade": "c",
            "ecoscore": "d",
            "nova_group": 3,
            "packaging": "plastic",
            "nutrition": {},
        }
        alt = _format_as_alternative(product, "cheaper")

        assert "Budget-friendly" in alt["why_this_tier"]
        assert "NOVA 3" in alt["trade_offs"]


class TestCategoryMapping:
    """Tests for category to OFF tag mapping."""

    def test_common_categories_mapped(self):
        """Test that common categories have OFF mappings."""
        common_categories = ["milk", "yogurt", "cheese", "bread", "chocolate", "tea"]
        for cat in common_categories:
            assert cat in CATEGORY_TO_OFF_TAG, f"'{cat}' not mapped"

    def test_mapping_format(self):
        """Test that mappings use correct OFF tag format."""
        for cat, tag in CATEGORY_TO_OFF_TAG.items():
            assert tag.startswith("en:"), f"Tag for '{cat}' doesn't start with 'en:'"


class TestGetProductByBarcode:
    """Tests for barcode lookup."""

    @patch("src.data_processing.open_food_facts._make_request")
    def test_successful_lookup(self, mock_request, mock_product_response):
        """Test successful product lookup by barcode."""
        mock_request.return_value = mock_product_response

        result = get_product_by_barcode("3017620422003")

        assert result is not None
        assert result["product_name"] == "Nutella"
        assert result["brand"] == "Ferrero"

    @patch("src.data_processing.open_food_facts._make_request")
    def test_product_not_found(self, mock_request):
        """Test handling of product not found."""
        mock_request.return_value = {"status": 0}

        result = get_product_by_barcode("0000000000")
        assert result is None

    @patch("src.data_processing.open_food_facts._make_request")
    def test_api_error(self, mock_request):
        """Test handling of API errors."""
        mock_request.return_value = None

        result = get_product_by_barcode("3017620422003")
        assert result is None


class TestSearchProducts:
    """Tests for product search."""

    @patch("src.data_processing.open_food_facts._make_request")
    def test_successful_search(self, mock_request, mock_search_response):
        """Test successful product search."""
        mock_request.return_value = mock_search_response

        results = search_products("milk")

        assert len(results) == 3
        assert results[0]["product_name"] == "Organic Whole Milk"

    @patch("src.data_processing.open_food_facts._make_request")
    def test_empty_search_results(self, mock_request):
        """Test handling of empty search results."""
        mock_request.return_value = {"products": []}

        results = search_products("nonexistent product xyz")
        assert results == []

    @patch("src.data_processing.open_food_facts._make_request")
    def test_search_with_category(self, mock_request, mock_search_response):
        """Test search with category filter."""
        mock_request.return_value = mock_search_response

        results = search_products("organic", category="en:milks")

        assert len(results) == 3
        # Verify category was passed in params (positional arg[1] is params dict)
        call_args = mock_request.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert "tagtype_0" in params


class TestSearchByCategory:
    """Tests for category-based search."""

    @patch("src.data_processing.open_food_facts._make_request")
    def test_successful_category_search(self, mock_request, mock_search_response):
        """Test successful category search."""
        mock_request.return_value = mock_search_response

        results = search_by_category("en:milks")

        assert len(results) == 3

    @patch("src.data_processing.open_food_facts._make_request")
    def test_category_search_with_nutrition_grade(self, mock_request, mock_search_response):
        """Test category search with nutrition grade filter."""
        mock_request.return_value = mock_search_response

        results = search_by_category("en:milks", nutrition_grade="a")

        # Verify nutrition grade was passed (positional arg[1] is params dict)
        call_args = mock_request.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert params["nutrition_grades_tags"] == "a"


class TestGetOffAlternativesForCategory:
    """Tests for the main fallback function."""

    @patch("src.data_processing.open_food_facts.search_by_category")
    def test_returns_alternatives_for_known_category(self, mock_search, mock_search_response):
        """Test getting alternatives for a known category."""
        mock_search.return_value = [
            _normalize_product(p) for p in mock_search_response["products"]
        ]

        result = get_off_alternatives_for_category("milk")

        assert result is not None
        assert "conscious" in result or "balanced" in result or "cheaper" in result

    @patch("src.data_processing.open_food_facts.search_by_category")
    @patch("src.data_processing.open_food_facts.search_products")
    def test_falls_back_to_text_search(self, mock_text_search, mock_cat_search, mock_search_response):
        """Test fallback to text search when category search fails."""
        mock_cat_search.return_value = []
        mock_text_search.return_value = [
            _normalize_product(p) for p in mock_search_response["products"]
        ]

        result = get_off_alternatives_for_category("milk")

        assert result is not None
        mock_text_search.assert_called_once()

    def test_unknown_category_returns_none(self):
        """Test that unknown categories return None without API call."""
        # "unknown_category_xyz" is not in CATEGORY_TO_OFF_TAG
        result = get_off_alternatives_for_category("unknown_category_xyz")
        assert result is None

    @patch("src.data_processing.open_food_facts.search_by_category")
    @patch("src.data_processing.open_food_facts.search_products")
    def test_returns_none_when_no_products(self, mock_text_search, mock_cat_search):
        """Test returns None when no products found."""
        mock_cat_search.return_value = []
        mock_text_search.return_value = []

        result = get_off_alternatives_for_category("milk")
        assert result is None


class TestFactsPackIntegration:
    """Tests for facts_pack.py integration with OFF."""

    @patch("src.data_processing.facts_pack.get_off_alternatives_for_category")
    def test_fallback_used_when_local_missing(self, mock_off):
        """Test that OFF fallback is used when local data is missing."""
        from src.data_processing.facts_pack import get_alternatives_for_category

        mock_off.return_value = {
            "cheaper": {"brand": "OFF Brand", "source": "open_food_facts"},
            "balanced": {"brand": "OFF Brand 2", "source": "open_food_facts"},
            "conscious": {"brand": "OFF Brand 3", "source": "open_food_facts"},
        }

        # Empty local data
        result = get_alternatives_for_category("milk", {}, use_off_fallback=True)

        assert result is not None
        assert result["cheaper"]["source"] == "open_food_facts"
        mock_off.assert_called_once_with("milk")

    def test_local_data_preferred_over_fallback(self):
        """Test that local data is used when available."""
        from src.data_processing.facts_pack import get_alternatives_for_category

        local_data = {
            "milk": {
                "cheaper": {"brand": "Local Brand", "source": "local"},
            }
        }

        result = get_alternatives_for_category("milk", local_data, use_off_fallback=True)

        assert result["cheaper"]["brand"] == "Local Brand"

    @patch("src.data_processing.facts_pack.get_off_alternatives_for_category")
    def test_fallback_disabled(self, mock_off):
        """Test that fallback can be disabled."""
        from src.data_processing.facts_pack import get_alternatives_for_category

        result = get_alternatives_for_category("milk", {}, use_off_fallback=False)

        assert result is None
        mock_off.assert_not_called()

"""
Tests for the facts_pack module.
"""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from src.data_processing.facts_pack import (
    generate_facts_pack,
    parse_user_input,
    parse_price,
    load_baseline,
    load_alternatives_from_csv,
    load_flags,
    get_baseline_for_category,
    get_alternatives_for_category,
    get_flags_for_category,
    validate_facts_pack,
    RECIPE_MAPPINGS,
    KEYWORD_CATEGORY_MAP,
    DEFAULT_USER_CONTEXT,
)


# Mock data fixtures
@pytest.fixture
def mock_baseline_data():
    """Mock baseline statistics data."""
    return {
        "summary": {
            "total_categories": 3,
            "total_items": 10,
            "total_purchases": 50,
        },
        "categories": {
            "produce_greens": {
                "median_price": 2.99,
                "price_range": [1.99, 5.99],
                "usual_brand": "Store Brand",
                "common_packaging": "plastic clamshell",
                "purchase_count": 20,
            },
            "produce_onions": {
                "median_price": 1.49,
                "price_range": [0.99, 2.99],
                "usual_brand": "Generic",
                "common_packaging": "loose",
                "purchase_count": 15,
            },
            "fermented": {
                "median_price": 7.99,
                "price_range": [5.99, 12.99],
                "usual_brand": "Miso Master",
                "common_packaging": "glass jar",
                "purchase_count": 10,
            },
        },
    }


@pytest.fixture
def mock_baseline_file(mock_baseline_data, tmp_path):
    """Create a temporary baseline JSON file."""
    filepath = tmp_path / "baseline_stats.json"
    with open(filepath, "w") as f:
        json.dump(mock_baseline_data, f)
    return filepath


@pytest.fixture
def mock_alternatives_csv(tmp_path):
    """Create a temporary alternatives CSV file."""
    csv_content = """,,,,,,,,,,,
Column 1,A,B,C,D,E,F,G,H,I,J,K
1,category,tier,brand,product_name,est_price,packaging,why_this_tier,certifications,trade_offs,source_url,source_reasoning
2,produce_greens,cheaper,Generic - Store Brand,Organic Red Kale,$1.99/lb,Loose bunch,Lowest-cost option,USDA Organic,Some trade-offs,https://example.com,Research
3,produce_greens,balanced,Generic - Store Brand,Organic Swiss Chard,$3.49/lb,Loose bunch,Moderate cost,USDA Organic,Moderate trade-offs,https://example.com,Research
4,produce_greens,conscious,Lancaster Farm Fresh,Local Organic Young Kale,$12.80/lb,Plastic clamshell,Premium sustainable,USDA Organic,Premium choice,https://example.com,Research
5,produce_onions,cheaper,Generic,Jumbo Yellow Onion,$0.99/lb,Loose bulk,Lowest cost,None,Basic option,https://example.com,Research
6,produce_onions,balanced,Generic,Sweet Onion,$1.49/lb,Loose bulk,Moderate price,None,Good value,https://example.com,Research
7,produce_onions,conscious,Lancaster Farm Fresh,Local Organic Yellow Onion,$1.99/lb,Loose bulk,Premium organic,USDA Organic,Best choice,https://example.com,Research
8,fermented,cheaper,Generic,White Miso,$4.99/ea,Plastic tub,Budget option,None,Basic miso,https://example.com,Research
9,fermented,balanced,Miso Master,Organic White Miso,$7.99/ea,Glass jar,Quality organic,USDA Organic,Good quality,https://example.com,Research
10,fermented,conscious,South River,Traditional Miso,$14.99/ea,Glass jar,Artisan crafted,"USDA Organic, Non-GMO",Premium artisan,https://example.com,Research
"""
    filepath = tmp_path / "alternatives.csv"
    with open(filepath, "w") as f:
        f.write(csv_content)
    return filepath


@pytest.fixture
def mock_flags_data():
    """Mock product flags data."""
    return {
        "produce_greens": [
            {"type": "seasonal", "message": "Peak season: Spring"}
        ],
        "fermented": [
            {"type": "recall", "message": "No active recalls", "status": "clear"}
        ],
    }


@pytest.fixture
def mock_flags_file(mock_flags_data, tmp_path):
    """Create a temporary flags JSON file."""
    filepath = tmp_path / "flags.json"
    with open(filepath, "w") as f:
        json.dump(mock_flags_data, f)
    return filepath


class TestParsePrice:
    """Tests for price parsing functionality."""

    def test_parse_simple_price(self):
        """Test parsing simple price format."""
        assert parse_price("$1.99/lb") == 1.99
        assert parse_price("$6.99") == 6.99

    def test_parse_complex_price(self):
        """Test parsing complex price formats."""
        assert parse_price("$6.99/ea (16oz = $0.44/oz)") == 6.99
        assert parse_price("$4.99/gallon ($0.04/fl oz)") == 4.99

    def test_parse_price_with_min(self):
        """Test parsing price with minimum purchase."""
        assert parse_price("$1.99/lb (min. 2lb)") == 1.99

    def test_parse_empty_price(self):
        """Test parsing empty/null prices."""
        assert parse_price("") is None
        assert parse_price(None) is None
        assert parse_price("null") is None

    def test_parse_no_dollar_sign(self):
        """Test parsing price without dollar sign."""
        assert parse_price("no price here") is None


class TestParseUserInput:
    """Tests for user input parsing functionality."""

    def test_recipe_matching_miso_soup(self):
        """Test matching miso soup recipe."""
        categories = parse_user_input("miso soup ingredients")
        assert "fermented" in categories
        assert "produce_greens" in categories
        assert "produce_onions" in categories

    def test_recipe_matching_salad(self):
        """Test matching salad recipe."""
        categories = parse_user_input("salad ingredients")
        assert "produce_greens" in categories
        assert "produce_tomatoes" in categories
        assert "produce_cucumbers" in categories

    def test_recipe_matching_smoothie(self):
        """Test matching smoothie recipe."""
        categories = parse_user_input("I want to make a smoothie")
        assert "fruit_berries" in categories
        assert "fruit_tropical" in categories
        assert "yogurt" in categories
        assert "milk" in categories

    def test_keyword_extraction_single(self):
        """Test extracting single keyword."""
        categories = parse_user_input("I need some spinach")
        assert categories == ["produce_greens"]

    def test_keyword_extraction_multiple(self):
        """Test extracting multiple keywords."""
        categories = parse_user_input("eggs and cheese please")
        assert "eggs" in categories
        assert "cheese" in categories

    def test_keyword_extraction_compound(self):
        """Test compound keyword extraction (longer keywords first)."""
        categories = parse_user_input("olive oil for cooking")
        assert "oils_olive" in categories

    def test_no_match_returns_empty(self):
        """Test that unrecognized input returns empty list."""
        categories = parse_user_input("something random")
        assert categories == []

    def test_case_insensitive(self):
        """Test that matching is case insensitive."""
        categories = parse_user_input("MISO SOUP")
        assert "fermented" in categories


class TestLoadBaseline:
    """Tests for baseline loading functionality."""

    def test_load_baseline_success(self, mock_baseline_file, mock_baseline_data):
        """Test successful baseline loading."""
        data = load_baseline(mock_baseline_file)
        assert data["summary"]["total_categories"] == 3
        assert "produce_greens" in data["categories"]

    def test_load_baseline_missing_file(self, tmp_path):
        """Test loading from missing file returns empty structure."""
        data = load_baseline(tmp_path / "nonexistent.json")
        assert data == {"summary": {}, "categories": {}}


class TestLoadAlternativesFromCSV:
    """Tests for alternatives CSV loading functionality."""

    def test_load_alternatives_success(self, mock_alternatives_csv):
        """Test successful alternatives loading from CSV."""
        data = load_alternatives_from_csv(mock_alternatives_csv)
        assert "produce_greens" in data
        assert "produce_onions" in data
        assert "fermented" in data

    def test_alternatives_tiers(self, mock_alternatives_csv):
        """Test that all tiers are loaded for each category."""
        data = load_alternatives_from_csv(mock_alternatives_csv)
        assert "cheaper" in data["produce_greens"]
        assert "balanced" in data["produce_greens"]
        assert "conscious" in data["produce_greens"]

    def test_alternatives_fields(self, mock_alternatives_csv):
        """Test that all fields are parsed correctly."""
        data = load_alternatives_from_csv(mock_alternatives_csv)
        cheaper = data["produce_greens"]["cheaper"]
        assert cheaper["brand"] == "Generic - Store Brand"
        assert cheaper["product_name"] == "Organic Red Kale"
        assert cheaper["est_price"] == 1.99
        assert cheaper["packaging"] == "Loose bunch"
        assert "USDA Organic" in cheaper["certifications"]

    def test_load_alternatives_missing_file(self, tmp_path):
        """Test loading from missing file returns empty dict."""
        data = load_alternatives_from_csv(tmp_path / "nonexistent.csv")
        assert data == {}


class TestLoadFlags:
    """Tests for flags loading functionality."""

    def test_load_flags_success(self, mock_flags_file, mock_flags_data):
        """Test successful flags loading."""
        data = load_flags(mock_flags_file)
        assert "produce_greens" in data
        assert data["produce_greens"][0]["type"] == "seasonal"

    def test_load_flags_missing_file(self, tmp_path):
        """Test loading from missing file returns empty dict."""
        data = load_flags(tmp_path / "nonexistent.json")
        assert data == {}


class TestGetBaselineForCategory:
    """Tests for getting baseline data for a specific category."""

    def test_get_existing_category(self, mock_baseline_data):
        """Test getting baseline for existing category."""
        result = get_baseline_for_category("produce_greens", mock_baseline_data)
        assert result is not None
        assert result["brand"] == "Store Brand"
        assert result["price"] == 2.99
        assert result["your_usual"] is True

    def test_get_nonexistent_category(self, mock_baseline_data):
        """Test getting baseline for nonexistent category."""
        result = get_baseline_for_category("nonexistent", mock_baseline_data)
        assert result is None


class TestGetAlternativesForCategory:
    """Tests for getting alternatives for a specific category."""

    def test_get_existing_alternatives(self, mock_alternatives_csv):
        """Test getting alternatives for existing category."""
        data = load_alternatives_from_csv(mock_alternatives_csv)
        result = get_alternatives_for_category("produce_greens", data)
        assert result is not None
        assert "cheaper" in result
        assert "balanced" in result
        assert "conscious" in result

    def test_get_nonexistent_alternatives(self, mock_alternatives_csv):
        """Test getting alternatives for nonexistent category."""
        data = load_alternatives_from_csv(mock_alternatives_csv)
        result = get_alternatives_for_category("nonexistent", data)
        assert result is None


class TestGetFlagsForCategory:
    """Tests for getting flags for a specific category."""

    def test_get_existing_flags(self, mock_flags_data):
        """Test getting flags for existing category."""
        result = get_flags_for_category("produce_greens", mock_flags_data)
        assert len(result) == 1
        assert result[0]["type"] == "seasonal"

    def test_get_nonexistent_flags(self, mock_flags_data):
        """Test getting flags for nonexistent category returns empty list."""
        result = get_flags_for_category("nonexistent", mock_flags_data)
        assert result == []


class TestValidateFactsPack:
    """Tests for facts pack validation."""

    def test_validate_valid_pack(self):
        """Test validation of a valid facts pack."""
        facts_pack = {
            "items": [
                {
                    "category": "produce_greens",
                    "baseline": {"price": 2.99},
                    "alternatives": {
                        "cheaper": {"brand": "Store Brand", "est_price": 1.99},
                        "balanced": {"brand": "Organic Brand", "est_price": 3.49},
                        "conscious": {"brand": "Premium Brand", "est_price": 12.80},
                    },
                }
            ]
        }
        is_valid, errors = validate_facts_pack(facts_pack)
        assert is_valid
        assert len(errors) == 0

    def test_validate_empty_items(self):
        """Test validation of empty items."""
        facts_pack = {"items": []}
        is_valid, errors = validate_facts_pack(facts_pack)
        assert not is_valid
        assert "No items in facts pack" in errors

    def test_validate_missing_alternatives(self):
        """Test validation catches missing alternatives."""
        facts_pack = {
            "items": [
                {
                    "category": "produce_greens",
                    "baseline": {"price": 2.99},
                    "alternatives": None,
                }
            ]
        }
        is_valid, errors = validate_facts_pack(facts_pack)
        assert not is_valid
        assert any("missing alternatives data" in e for e in errors)

    def test_validate_missing_tier(self):
        """Test validation catches missing tier."""
        facts_pack = {
            "items": [
                {
                    "category": "produce_greens",
                    "baseline": {"price": 2.99},
                    "alternatives": {
                        "cheaper": {"brand": "Store Brand"},
                        "balanced": {"brand": "Organic Brand"},
                        # missing "conscious" tier
                    },
                }
            ]
        }
        is_valid, errors = validate_facts_pack(facts_pack)
        assert not is_valid
        assert any("missing 'conscious'" in e for e in errors)

    def test_validate_missing_brand(self):
        """Test validation catches missing brand."""
        facts_pack = {
            "items": [
                {
                    "category": "produce_greens",
                    "baseline": {"price": 2.99},
                    "alternatives": {
                        "cheaper": {"brand": "", "est_price": 1.99},
                        "balanced": {"brand": "Organic Brand", "est_price": 3.49},
                        "conscious": {"brand": "Premium Brand", "est_price": 12.80},
                    },
                }
            ]
        }
        is_valid, errors = validate_facts_pack(facts_pack)
        assert not is_valid
        assert any("'cheaper' tier missing brand" in e for e in errors)

    def test_validate_unreasonable_price(self):
        """Test validation catches unreasonable prices."""
        facts_pack = {
            "items": [
                {
                    "category": "produce_greens",
                    "baseline": {"price": -1.00},  # negative price
                    "alternatives": {
                        "cheaper": {"brand": "Store Brand", "est_price": 1.99},
                        "balanced": {"brand": "Organic Brand", "est_price": 3.49},
                        "conscious": {"brand": "Premium Brand", "est_price": 12.80},
                    },
                }
            ]
        }
        is_valid, errors = validate_facts_pack(facts_pack)
        assert not is_valid
        assert any("out of reasonable range" in e for e in errors)


class TestGenerateFactsPack:
    """Tests for the main generate_facts_pack function."""

    def test_generate_miso_soup_pack(
        self, mock_baseline_file, mock_alternatives_csv, mock_flags_file
    ):
        """Test generating facts pack for miso soup."""
        facts_pack = generate_facts_pack(
            "miso soup ingredients",
            baseline_path=mock_baseline_file,
            alternatives_path=mock_alternatives_csv,
            flags_path=mock_flags_file,
        )

        assert facts_pack["request"] == "miso soup ingredients"
        assert len(facts_pack["items"]) == 3  # fermented, produce_greens, produce_onions
        assert facts_pack["user_context"] == DEFAULT_USER_CONTEXT

        # Check categories are present
        categories = [item["category"] for item in facts_pack["items"]]
        assert "fermented" in categories
        assert "produce_greens" in categories
        assert "produce_onions" in categories

    def test_generate_with_custom_context(
        self, mock_baseline_file, mock_alternatives_csv, mock_flags_file
    ):
        """Test generating facts pack with custom user context."""
        custom_context = {
            "budget_priority": "high",
            "health_priority": "high",
            "packaging_priority": "low",
        }
        facts_pack = generate_facts_pack(
            "miso soup",
            user_context=custom_context,
            baseline_path=mock_baseline_file,
            alternatives_path=mock_alternatives_csv,
            flags_path=mock_flags_file,
        )

        assert facts_pack["user_context"] == custom_context

    def test_generate_includes_baseline(
        self, mock_baseline_file, mock_alternatives_csv, mock_flags_file
    ):
        """Test that facts pack includes baseline data."""
        facts_pack = generate_facts_pack(
            "kale",
            baseline_path=mock_baseline_file,
            alternatives_path=mock_alternatives_csv,
            flags_path=mock_flags_file,
        )

        greens_item = next(
            (i for i in facts_pack["items"] if i["category"] == "produce_greens"), None
        )
        assert greens_item is not None
        assert greens_item["baseline"]["brand"] == "Store Brand"
        assert greens_item["baseline"]["price"] == 2.99
        assert greens_item["baseline"]["your_usual"] is True

    def test_generate_includes_alternatives(
        self, mock_baseline_file, mock_alternatives_csv, mock_flags_file
    ):
        """Test that facts pack includes alternatives data."""
        facts_pack = generate_facts_pack(
            "kale",
            baseline_path=mock_baseline_file,
            alternatives_path=mock_alternatives_csv,
            flags_path=mock_flags_file,
        )

        greens_item = next(
            (i for i in facts_pack["items"] if i["category"] == "produce_greens"), None
        )
        assert greens_item is not None
        assert "cheaper" in greens_item["alternatives"]
        assert "balanced" in greens_item["alternatives"]
        assert "conscious" in greens_item["alternatives"]

    def test_generate_includes_flags(
        self, mock_baseline_file, mock_alternatives_csv, mock_flags_file
    ):
        """Test that facts pack includes flags data."""
        facts_pack = generate_facts_pack(
            "kale",
            baseline_path=mock_baseline_file,
            alternatives_path=mock_alternatives_csv,
            flags_path=mock_flags_file,
        )

        greens_item = next(
            (i for i in facts_pack["items"] if i["category"] == "produce_greens"), None
        )
        assert greens_item is not None
        assert len(greens_item["flags"]) == 1
        assert greens_item["flags"][0]["type"] == "seasonal"

    def test_generate_empty_input(
        self, mock_baseline_file, mock_alternatives_csv, mock_flags_file
    ):
        """Test generating facts pack for unrecognized input."""
        facts_pack = generate_facts_pack(
            "something unrecognizable",
            baseline_path=mock_baseline_file,
            alternatives_path=mock_alternatives_csv,
            flags_path=mock_flags_file,
        )

        assert facts_pack["request"] == "something unrecognizable"
        assert len(facts_pack["items"]) == 0
        assert "validation_warnings" in facts_pack

    def test_generate_adds_validation_warnings(
        self, mock_baseline_file, mock_flags_file, tmp_path
    ):
        """Test that validation warnings are added to facts pack."""
        # Create CSV with missing brand
        csv_content = """,,,,,,,,,,,
Column 1,A,B,C,D,E,F,G,H,I,J,K
1,category,tier,brand,product_name,est_price,packaging,why_this_tier,certifications,trade_offs,source_url,source_reasoning
2,produce_greens,cheaper,,No Brand,$1.99/lb,Loose,Budget,None,Trade-offs,https://example.com,Research
3,produce_greens,balanced,Brand,Product,$3.49/lb,Pack,Mid,None,Trade-offs,https://example.com,Research
4,produce_greens,conscious,Brand,Product,$12.80/lb,Pack,Premium,None,Trade-offs,https://example.com,Research
"""
        csv_path = tmp_path / "incomplete_alternatives.csv"
        with open(csv_path, "w") as f:
            f.write(csv_content)

        facts_pack = generate_facts_pack(
            "kale",
            baseline_path=mock_baseline_file,
            alternatives_path=csv_path,
            flags_path=mock_flags_file,
        )

        assert "validation_warnings" in facts_pack
        assert any("missing brand" in w for w in facts_pack["validation_warnings"])


class TestRecipeMappings:
    """Tests for recipe mapping coverage."""

    def test_all_recipes_have_valid_categories(self):
        """Test that all recipe mappings use valid categories."""
        all_categories = set(KEYWORD_CATEGORY_MAP.values())
        for recipe, categories in RECIPE_MAPPINGS.items():
            for cat in categories:
                # Category should either be in keyword map values or be a known category
                assert cat in all_categories or cat in [
                    "yogurt", "cheese", "eggs", "butter_ghee", "bread",
                    "oils_olive", "oils_other", "spices", "canned_coconut",
                    "hummus_dips", "produce_aromatics", "produce_cucumbers",
                ], f"Unknown category '{cat}' in recipe '{recipe}'"

    def test_recipe_mappings_not_empty(self):
        """Test that recipe mappings are not empty."""
        assert len(RECIPE_MAPPINGS) > 0
        for recipe, categories in RECIPE_MAPPINGS.items():
            assert len(categories) > 0, f"Recipe '{recipe}' has no categories"


class TestKeywordCategoryMap:
    """Tests for keyword to category mapping coverage."""

    def test_common_ingredients_covered(self):
        """Test that common ingredients are mapped."""
        common_ingredients = [
            "milk", "eggs", "cheese", "bread", "butter",
            "spinach", "kale", "onion", "tomato", "carrot",
            "apple", "banana", "chicken", "rice", "pasta",
        ]
        for ingredient in common_ingredients:
            assert ingredient in KEYWORD_CATEGORY_MAP, f"'{ingredient}' not in keyword map"

    def test_no_empty_categories(self):
        """Test that no keywords map to empty categories."""
        for keyword, category in KEYWORD_CATEGORY_MAP.items():
            assert category, f"Keyword '{keyword}' maps to empty category"
            assert len(category) > 0, f"Keyword '{keyword}' maps to empty category"

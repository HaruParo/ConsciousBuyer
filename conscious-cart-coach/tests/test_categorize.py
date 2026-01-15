"""
Tests for the categorize module.
"""

import pytest

from src.data_processing.categorize import (
    categorize_item,
    _match_patterns,
    _get_category_from_brand,
    MANUAL_OVERRIDES,
)


class TestPatternMatching:
    """Tests for pattern matching functionality."""

    def test_match_simple_pattern(self):
        """Test matching a simple word pattern."""
        assert _match_patterns("Organic Whole Milk", [r"\bmilk\b"])
        assert _match_patterns("2% Milk Carton", [r"\bmilk\b"])

    def test_match_case_insensitive(self):
        """Test that matching is case insensitive."""
        assert _match_patterns("ORGANIC MILK", [r"\bmilk\b"])
        assert _match_patterns("organic milk", [r"\bmilk\b"])
        assert _match_patterns("Organic Milk", [r"\bmilk\b"])

    def test_no_match(self):
        """Test that non-matching text returns False."""
        assert not _match_patterns("Organic Cheese", [r"\bmilk\b"])
        assert not _match_patterns("", [r"\bmilk\b"])
        assert not _match_patterns(None, [r"\bmilk\b"])

    def test_match_multiple_patterns(self):
        """Test matching against multiple patterns."""
        patterns = [r"\bmilk\b", r"\byogurt\b", r"\bcheese\b"]
        assert _match_patterns("Greek Yogurt", patterns)
        assert _match_patterns("Cheddar Cheese", patterns)
        assert _match_patterns("Whole Milk", patterns)
        assert not _match_patterns("Bread Loaf", patterns)

    def test_match_compound_pattern(self):
        """Test matching compound patterns."""
        assert _match_patterns("Extra Virgin Olive Oil", [r"olive\s*oil"])
        assert _match_patterns("Coconut Oil Organic", [r"coconut\s*oil"])


class TestBrandCategoryHints:
    """Tests for brand-based category hints."""

    def test_driscoll_berries(self):
        """Test Driscoll's maps to berries."""
        assert _get_category_from_brand("Driscoll's") == "fruit_berries"

    def test_farmer_focus_chicken(self):
        """Test Farmer Focus maps to chicken."""
        assert _get_category_from_brand("Farmer Focus") == "chicken"

    def test_vital_farms_eggs(self):
        """Test Vital Farms maps to eggs."""
        assert _get_category_from_brand("Vital Farms") == "eggs"

    def test_bread_alone_bread(self):
        """Test Bread Alone maps to bread."""
        assert _get_category_from_brand("Bread Alone") == "bread"

    def test_unknown_brand(self):
        """Test unknown brand returns None."""
        assert _get_category_from_brand("Unknown Brand") is None
        assert _get_category_from_brand("Store Brand") is None
        assert _get_category_from_brand(None) is None

    def test_case_insensitive_brand(self):
        """Test brand matching is case insensitive."""
        assert _get_category_from_brand("DRISCOLL'S") == "fruit_berries"
        assert _get_category_from_brand("driscoll's") == "fruit_berries"


class TestCategorizeItem:
    """Tests for the main categorize_item function."""

    # Dairy & Eggs
    def test_milk_products(self):
        """Test milk categorization."""
        assert categorize_item("Alexandre A2/A2 Organic 4% Whole Milk, Carton") == "milk"
        assert categorize_item("Ronnybrook Farm Dairy Creamline Whole Milk") == "milk"
        assert categorize_item("Small Creamline Whole Milk") == "milk"

    def test_yogurt_products(self):
        """Test yogurt categorization."""
        assert categorize_item("Hawthorne Valley Farm Organic Plain Biodynamic Yogurt") == "yogurt"
        assert categorize_item("White Moustache Handmade Yogurt, Greek") == "yogurt"

    def test_cheese_products(self):
        """Test cheese categorization."""
        assert categorize_item("Organic Sliced Mild Cheddar") == "cheese"
        assert categorize_item("Organic Sliced Swiss Cheese") == "cheese"
        assert categorize_item("Organic Paneer") == "cheese"

    def test_eggs_products(self):
        """Test eggs categorization."""
        assert categorize_item("Vital Farms Pasture-Raised Organic Large Eggs") == "eggs"
        assert categorize_item("Pasture Raised Eggs") == "eggs"

    def test_ice_cream_products(self):
        """Test ice cream categorization."""
        assert categorize_item("Van Leeuwen Ice Cream, Sicilian Pistachio") == "ice_cream"
        assert categorize_item("Bubbies Mochi Ice Cream, Pistachio") == "ice_cream"

    # Proteins
    def test_chicken_products(self):
        """Test chicken categorization."""
        assert categorize_item("Farmer Focus Organic Boneless Skinless Chicken Breast") == "chicken"
        assert categorize_item("Farmer Focus Organic Chicken Wings") == "chicken"

    # Nuts
    def test_nuts_almonds(self):
        """Test almonds categorization."""
        assert categorize_item("Just FreshDirect Organic Raw Almonds") == "nuts_almonds"

    def test_nuts_cashews(self):
        """Test cashews categorization."""
        assert categorize_item("Just FreshDirect Organic Raw Cashews") == "nuts_cashews"

    def test_nuts_peanuts(self):
        """Test peanuts categorization."""
        assert categorize_item("Just FreshDirect Roasted Unsalted Peanuts") == "nuts_peanuts"

    # Bread & Grains
    def test_bread_products(self):
        """Test bread categorization."""
        assert categorize_item("Bread Alone Organic San Francisco Sourdough") == "bread"
        assert categorize_item("Black Seed Bagels Everything Bagels") == "bread"
        assert categorize_item("Multigrain Sourdough English Muffins") == "bread"

    def test_grains_products(self):
        """Test grains categorization."""
        assert categorize_item("Bob's Red Mill Organic Quinoa") == "grains"

    # Produce - Onions
    def test_produce_onions(self):
        """Test onions/alliums categorization."""
        assert categorize_item("Red Onions") == "produce_onions"
        assert categorize_item("Organic Red Onions") == "produce_onions"
        assert categorize_item("Shallots") == "produce_onions"
        assert categorize_item("Organic Garlic") == "produce_onions"
        assert categorize_item("Organic Leeks, Bunch") == "produce_onions"
        assert categorize_item("Organic Scallions") == "produce_onions"

    # Produce - Tomatoes
    def test_produce_tomatoes(self):
        """Test tomatoes categorization."""
        assert categorize_item("Organic Roma Tomatoes") == "produce_tomatoes"
        assert categorize_item("Plum Tomatoes") == "produce_tomatoes"
        assert categorize_item("Lancaster Farm Fresh Cooperative Local Organic Heirloom Tomatoes") == "produce_tomatoes"

    # Produce - Cucumbers
    def test_produce_cucumbers(self):
        """Test cucumbers categorization."""
        assert categorize_item("Green Cucumber") == "produce_cucumbers"
        assert categorize_item("Organic Persian Cucumbers") == "produce_cucumbers"
        assert categorize_item("Organic Slicing Cucumbers") == "produce_cucumbers"

    # Produce - Greens
    def test_produce_greens(self):
        """Test greens categorization."""
        assert categorize_item("Organic Baby Spinach") == "produce_greens"
        assert categorize_item("Organic Green Kale") == "produce_greens"
        assert categorize_item("Organic Swiss Chard") == "produce_greens"
        assert categorize_item("Organic Basil") == "produce_greens"
        assert categorize_item("Organic Broccoli") == "produce_greens"

    # Produce - Root Vegetables
    def test_produce_root_veg(self):
        """Test root vegetables categorization."""
        assert categorize_item("Cal-Organic Organic Rainbow Carrots") == "produce_root_veg"
        assert categorize_item("Loose Organic Beets") == "produce_root_veg"
        assert categorize_item("Organic Japanese Sweet Potatoes") == "produce_root_veg"
        assert categorize_item("Organic Ginger Root") == "produce_root_veg"

    # Produce - Squash
    def test_produce_squash(self):
        """Test squash categorization."""
        assert categorize_item("Organic Acorn Squash") == "produce_squash"
        assert categorize_item("Organic Green Zucchini") == "produce_squash"
        assert categorize_item("Chinese Eggplant") == "produce_squash"
        assert categorize_item("Chayote Squash") == "produce_squash"

    # Produce - Beans
    def test_produce_beans(self):
        """Test beans categorization."""
        assert categorize_item("Organic Green Beans") == "produce_beans"
        assert categorize_item("Chinese Long Beans") == "produce_beans"
        assert categorize_item("Seapoint Farms Edamame Organic Shelled Soybeans") == "produce_beans"
        assert categorize_item("Organic Okra") == "produce_beans"

    # Fruits - Berries
    def test_fruit_berries(self):
        """Test berries categorization."""
        assert categorize_item("Driscoll's Organic Strawberries") == "fruit_berries"
        assert categorize_item("Driscoll's Organic Blackberries") == "fruit_berries"
        assert categorize_item("Organic Blueberries") == "fruit_berries"

    # Fruits - Tropical
    def test_fruit_tropical(self):
        """Test tropical fruits categorization."""
        assert categorize_item("Baby Bananas, Bunch") == "fruit_tropical"
        assert categorize_item("Organic Tommy Atkins Mango") == "fruit_tropical"
        assert categorize_item("Organic Golden Pineapple") == "fruit_tropical"
        assert categorize_item("Organic Hass Avocados") == "fruit_tropical"

    # Fruits - Citrus
    def test_fruit_citrus(self):
        """Test citrus categorization."""
        assert categorize_item("Organic Lemons") == "fruit_citrus"
        assert categorize_item("Limes") == "fruit_citrus"
        assert categorize_item("Organic Navel Orange") == "fruit_citrus"
        assert categorize_item("Organic Pink Grapefruit") == "fruit_citrus"

    # Oils
    def test_oils_olive(self):
        """Test olive oil categorization."""
        assert categorize_item("Aria Extra Virgin Olive Oil") == "oils_olive"
        assert categorize_item("La Tourangelle Organic Extra Virgin Olive Oil") == "oils_olive"

    def test_oils_coconut(self):
        """Test coconut oil categorization."""
        assert categorize_item("Nutiva Organic Coconut Oil") == "oils_coconut"
        assert categorize_item("Spectrum Organic Virgin Coconut Oil, Unrefined (for Medium Heat)") == "oils_coconut"

    # Vinegar
    def test_vinegar(self):
        """Test vinegar categorization."""
        assert categorize_item("Bragg Organic Raw Unfiltered Apple Cider Vinegar") == "vinegar"
        assert categorize_item("De Nigris Organic White Wine Vinegar") == "vinegar"

    # Spices
    def test_spices(self):
        """Test spices categorization."""
        assert categorize_item("Burlap & Barrel New Harvest Turmeric") == "spices"
        assert categorize_item("Burlap & Barrel Wild Mountain Cumin") == "spices"
        assert categorize_item("Morton Iodized Salt") == "spices"
        assert categorize_item("Simply Organic Crushed Red Pepper") == "spices"

    # Fermented
    def test_fermented(self):
        """Test fermented foods categorization."""
        assert categorize_item("Miso Master Organic Traditional Red Miso") == "fermented"
        assert categorize_item("Mama O's OG Kimchi") == "fermented"
        assert categorize_item("Pickled Daikon Kimchi") == "fermented"

    # Chocolate
    def test_chocolate(self):
        """Test chocolate categorization."""
        assert categorize_item("Beyond Good 85% Sea Salt Dark Chocolate Bar") == "chocolate"
        assert categorize_item("Hu Kitchen Simple Organic Dark Chocolate Bar") == "chocolate"

    # Cookies
    def test_cookies(self):
        """Test cookies categorization."""
        assert categorize_item("Mulino Bianco Galletti, Shortbread with Sugar Crystals Cookies") == "cookies_crackers"
        assert categorize_item("Rustic Bakery Shortbread Cookies, Vanilla") == "cookies_crackers"

    # Personal Care
    def test_personal_care(self):
        """Test personal care categorization."""
        assert categorize_item("Sensodyne Pronamel Gentle Whitening Toothpaste, Alpine Breeze") == "personal_care"
        assert categorize_item("Sensodyne Repair & Protect Whitening Toothpaste") == "personal_care"


class TestManualOverrides:
    """Tests for manual override functionality."""

    def test_manual_override_chips(self):
        """Test chips manual overrides."""
        assert categorize_item("Sour Cream & Onion Chips") == "chips"
        assert categorize_item("Sweet Potato Chips") == "chips"

    def test_manual_override_hummus(self):
        """Test hummus manual override."""
        assert categorize_item("Zesty Za'atar Hummus") == "hummus_dips"

    def test_manual_override_frozen(self):
        """Test frozen items manual override."""
        assert categorize_item("Headwater Food Hub Frozen Peas") == "frozen_veg"

    def test_manual_override_coconut(self):
        """Test coconut products manual overrides."""
        assert categorize_item("Fresh Coconut Chunks") == "fruit_tropical"
        assert categorize_item("Organic Coconut Milk") == "canned_coconut"


class TestBrandFallback:
    """Tests for brand-based fallback categorization."""

    def test_brand_fallback_berries(self):
        """Test that Driscoll's brand helps categorize ambiguous items."""
        # Even without clear berry name, brand should help
        result = categorize_item("Driscoll's Limited Edition Sweetest Batch Strawberries", "Driscoll's")
        assert result == "fruit_berries"

    def test_brand_fallback_ice_cream(self):
        """Test ice cream brand fallback."""
        result = categorize_item("New City Microcreamery Ice Cream, Baklava", "New City Microcreamery")
        assert result == "ice_cream"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_name(self):
        """Test handling of empty item name."""
        assert categorize_item("") == "uncategorized"

    def test_none_brand(self):
        """Test handling of None brand."""
        result = categorize_item("Organic Whole Milk", None)
        assert result == "milk"

    def test_compound_names(self):
        """Test items with multiple potential categories pick the right one."""
        # "Sweet Potato" should be root_veg, not chips
        assert categorize_item("Organic Sweet Potatoes") == "produce_root_veg"

    def test_priority_ordering(self):
        """Test that higher priority categories match first."""
        # "Olive Oil" should be oils_olive (priority 10), not oils_other (priority 5)
        assert categorize_item("Extra Virgin Olive Oil") == "oils_olive"

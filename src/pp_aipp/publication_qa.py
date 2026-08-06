"""Deterministic publication edits for legacy Project Physique recipes."""

from __future__ import annotations

import re
from collections.abc import Iterable

SEAFOOD = ("salmon", "cod", "haddock", "tuna", "mackerel", "prawn", "shrimp", "fish")
POULTRY = ("chicken", "turkey")
PORK = ("pork", "ham", "bacon")
BEEF = ("beef", "steak")
PLANT = ("lentil", "chickpea", "bean", "tofu", "aubergine")
STARCHES = (
    "basmati rice", "jasmine rice", "brown rice", "rice noodles", "egg noodles",
    "wholewheat pasta", "wholemeal pasta", "dried white pasta", "orzo", "quinoa",
    "pearl barley", "bulgur wheat", "pearl couscous", "wholewheat couscous",
    "plain couscous", "potatoes", "baby potatoes", "sweet potato",
)


def _joined(names: Iterable[str]) -> str:
    return " ".join(str(name).lower() for name in names)


def _has(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _first_name(names: list[str], terms: tuple[str, ...], fallback: str) -> str:
    for name in names:
        if _has(name.lower(), terms):
            return name
    return fallback


def _starch_instruction(names: list[str]) -> str | None:
    starch = _first_name(names, STARCHES, "")
    if not starch:
        return None
    lower = starch.lower()
    if "potato" in lower:
        return f"Boil or roast the {lower} until tender, then keep warm."
    return f"Cook the {lower} according to the packet instructions; drain if necessary and keep warm."


def polish_method_text(text: str, ingredient_names: Iterable[str]) -> str:
    """Return a recipe-aware replacement for known legacy template language."""
    names = [str(name).strip() for name in ingredient_names if str(name).strip()]
    ingredients = _joined(names)
    seafood = _has(ingredients, SEAFOOD)
    poultry = _has(ingredients, POULTRY)
    pork = _has(ingredients, PORK)
    beef = _has(ingredients, BEEF)
    plant = _has(ingredients, PLANT) and not (seafood or poultry or pork or beef)

    if re.search(r"^Cook the .+ according to the packet instructions, or roast/boil until tender\.$", text):
        return _starch_instruction(names) or text
    if re.search(r"^Cook the grain or potatoes according to the packet instructions", text):
        return _starch_instruction(names) or "Prepare the vegetables as described below."

    if "poultry and pork must reach 75°C, while fish should flake easily" in text:
        prefix = text.split(";", 1)[0].replace("until browned and safely cooked", "until browned")
        if seafood:
            return f"{prefix} and opaque, and check that it flakes easily."
        if poultry or pork:
            return f"{prefix} and cooked through to 75°C."
        if beef:
            return f"{prefix} and cooked to your preferred doneness."
        if plant:
            return f"{prefix} and piping hot throughout."

    if "poultry must reach 75°C" in text:
        prefix = text.split(";", 1)[0]
        if poultry:
            return f"{prefix}; check the poultry reaches 75°C in the centre."
        return f"{prefix}."

    if text.startswith("Check poultry or pork reaches 75°C; fish should flake easily."):
        if seafood:
            return "Check the fish is opaque and flakes easily, then serve immediately."
        if poultry:
            return "Check the poultry reaches 75°C in the centre, then rest for 3–5 minutes before serving."
        if pork:
            return "Check the pork reaches 75°C in the centre, then rest for 3–5 minutes before serving."
        if beef:
            return "Cook the beef to your preferred doneness, then rest for 3–5 minutes before serving."

    if text.startswith("Rest meat for 3–5 minutes where appropriate"):
        suffix = "then plate with the vegetables and starch and spoon over any pan juices."
        if seafood:
            return f"Let the fish rest for 1–2 minutes, {suffix}"
        if plant:
            return f"Let the dish stand for 2 minutes, {suffix}"
        return f"Rest the cooked protein for 3–5 minutes, {suffix}"

    text = text.replace(
        "with the measured garlic, herbs, mustard, lemon or other flavourings.",
        "with the listed garlic, herbs and seasonings.",
    )
    text = text.replace(
        "Combine the grain and vegetables with the measured lemon, soy sauce or oil dressing.",
        "Combine the prepared grain and vegetables with the listed dressing ingredients.",
    )
    text = text.replace(
        "Slice or flake the protein, arrange over the bowl or salad, add cheese, nuts or seeds, and serve.",
        "Slice or flake the cooked protein, arrange it over the bowl or salad, finish with the remaining listed ingredients and serve.",
    )
    text = text.replace("arrange it over the bread", "arrange them over the bread")
    text = text.replace("tomato purée, if listed, and ", "tomato purée and ") if "tomato purée" in ingredients else text.replace(" and tomato purée, if listed,", "")
    text = text.replace(" as needed", "")

    return text


SPECIAL_METHODS: dict[str, tuple[str, ...]] = {
    "PP-R010": (
        "Warm the cooked lentils gently and keep them covered.",
        "Season the cod with the garlic, mustard, lemon juice, parsley and dried herbs.",
        "Heat half the oil in a non-stick pan and cook the cod until opaque and it flakes easily.",
        "Toss the spinach, tomatoes, red onion and warm lentils with the remaining oil and lemon juice.",
        "Divide the warm lentil salad between plates, top with the cod and serve.",
    ),
    "PP-R047": (
        "Steam the cauliflower until tender, then mash with half the light butter and keep warm.",
        "Pat the haddock dry and season with garlic and black pepper.",
        "Heat a non-stick pan and cook the haddock until opaque and it flakes easily.",
        "Steam the green beans until tender-crisp; melt the remaining butter with the parsley.",
        "Serve the haddock with the cauliflower mash and green beans, then spoon over the garlic-parsley butter.",
    ),
    "PP-R050": (
        "Heat the oven to 200°C fan (220°C conventional) and line a large roasting tray.",
        "Cut the courgette and aubergine into even pieces, then add them to the tray with the cherry tomatoes and chickpeas.",
        "Coat the chicken with the olive oil, garlic and oregano, then nestle it among the vegetables.",
        "Roast for 25–30 minutes, turning the vegetables once, until the chicken reaches 75°C and the vegetables are tender.",
        "Rest the chicken for 3–5 minutes, then divide the tray bake between plates and serve.",
    ),
    "PP-R067": (
        "Heat the oven to 200°C fan (220°C conventional) and line a large roasting tray.",
        "Cut the butternut squash, courgette and red onion into even pieces.",
        "Toss the vegetables with the olive oil, cumin and coriander, then roast for 25–30 minutes until tender.",
        "Warm the cooked lentils, fold through the roasted vegetables and check the dish is piping hot.",
        "Finish with fresh parsley and serve.",
    ),
    "PP-R076": (
        "Heat the oven to 200°C fan (220°C conventional) and lightly oil a baking dish.",
        "Cut the aubergine and red onion into even pieces, then toss with the oil, garlic and oregano.",
        "Roast for 20 minutes, turning once, until the aubergine begins to soften.",
        "Stir in the lentils and cherry tomatoes, top with feta and bake for 10–15 minutes until piping hot.",
        "Let the bake stand for 5 minutes before serving.",
    ),
    "PP-R071": (
        "Bring the cooked beetroot to room temperature and wash and dry the rocket.",
        "Season the beef steak and heat a non-stick pan until hot.",
        "Cook the steak to your preferred doneness, then rest it for 3–5 minutes.",
        "Toss the beetroot and rocket with the olive oil and lemon juice.",
        "Slice the steak, arrange it over the salad, crumble over the feta, add the walnuts and serve.",
    ),
    "PP-R075": (
        "Heat the oven to 200°C fan (220°C conventional) and line a roasting tray.",
        "Cut the beetroot into even pieces, toss with half the oil and roast for 20 minutes.",
        "Coat the pork with the remaining oil, Dijon mustard, garlic and thyme.",
        "Add the pork and green beans to the tray and roast until the pork reaches 75°C and the vegetables are tender.",
        "Rest the pork for 3–5 minutes before slicing and serving with the roasted vegetables.",
    ),
    "PP-R079": (
        "Cook the brown basmati rice according to the packet instructions and keep warm.",
        "Heat a deep pan over medium heat and soften the onion, garlic and ginger for 3–4 minutes with a splash of water.",
        "Add the curry powder and cook for 30 seconds, then stir in the cauliflower and butter beans.",
        "Pour in the coconut milk and simmer for 12–18 minutes until the cauliflower is tender and the curry is piping hot.",
        "Taste, adjust the seasoning and serve with the brown basmati rice.",
    ),
}


def polished_method_steps(recipe_id: str, method: Iterable[dict], ingredient_names: Iterable[str]) -> list[dict]:
    """Return publication-ready dictionary steps without mutating the source."""
    names = list(ingredient_names)
    if recipe_id in SPECIAL_METHODS:
        return [{"number": index, "text": value} for index, value in enumerate(SPECIAL_METHODS[recipe_id], 1)]
    return [{**step, "text": polish_method_text(str(step.get("text", "")), names)} for step in method]


def polish_domain_recipe(recipe) -> None:
    """Apply the same edits to a parsed domain Recipe before it is stored."""
    names = [item.name for item in recipe.ingredients]
    if recipe.recipe_id in SPECIAL_METHODS and recipe.method:
        step_type = type(recipe.method[0])
        recipe.method = [step_type(number=i, text=value) for i, value in enumerate(SPECIAL_METHODS[recipe.recipe_id], 1)]
        return
    for step in recipe.method:
        step.text = polish_method_text(step.text, names)

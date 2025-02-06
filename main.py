from pathlib import Path
import json
import copy
from PIL import Image


class Item:
    def __init__(self, item_id, data, lang, _settings):
        self.components = {}
        self.id = item_id
        self.data = data
        self.lang = lang
        self.settings = _settings
        self.namespace = _settings.namespace
        self.base_item = self.data.get("base", "minecraft:poisonous_potato")

    def __str__(self):
        return f"ID: {self.id}\nData: {self.data}"

    def make(self):
        self.lang[f"item.{self.namespace}.{self.id}"] = self.data.get("name")
        components = self.data.get("components", {})

        if "template" in self.data:
            input_custom_data = self.data.get("custom_data", {})
            check_templates(self, self.data.get("template"))
            self.data.get("custom_data", {}).update(input_custom_data)

        self.data.get("components",{}).update(components)
        self.make_components()

        self.make_loot_table()
        if "recipe" in self.data:
            self.make_recipe(self.data.get("recipe"))

        if "item" in self.data:
            self.make_item()

        if "model" in self.data:
            self.make_model()

        if "texture" in self.data:
            self.make_texture(self.data.get("texture"))

    def make_texture(self, texture):
        if isinstance(texture, dict) and self.settings.sprites:
            x, y = texture.get("x", 0), texture.get("y", 0)
            search = texture.get("search", "texture")
            if search == "pixel":
                x = x // 16
                y = y // 16
            self.make_texture_from_spritesheet(x, y)

    def make_texture_from_spritesheet(self, x, y):
        texture_path = self.settings.get_path("textures") / f"{self.id}.png"
        if 0 <= y < len(self.settings.sprites) and 0 <= x < len(self.settings.sprites[0]):
            texture = self.settings.sprites[y][x]
            if texture:
                texture.save(texture_path)
                print(f"Created ...{Path(*texture_path.parts[-4:])}")
            else:
                print("Selected does not exist.")
        else:
            print("Invalid texture index.")

    def make_lore(self, lore):
        return [
            {
                "translate": f"item.{self.namespace}.{self.id}.lore{n}",
                "color": lore.get("color", "gray"),
                "italic": lore.get("italic", False),
            }
            for n, text in enumerate(lore.get("contents", []))
            if self.lang.setdefault(f"item.{self.namespace}.{self.id}.lore{n}", text) is not None
        ]

    def make_model(self):
        model_path = self.settings.get_path("models")
        model = self.data.get("model")
        self.make_model_json(model, model_path / f"{self.id}.json",self.id)

    def make_model_json(self, model, model_path,item_id):
        if isinstance(model, str):
            model = {
                "parent": model,
                "textures": {
                    "layer0": f"{self.settings.namespace}:item/{item_id}"
                }
            }
        write_json(model_path, model, self.settings.indent)

    def make_item(self):
        item_path = self.settings.get_path("items") / f"{self.id}.json"
        item = self.data.get("item")
        item = item.copy() if isinstance(item, dict) else item
        if item == "simple":
            item = {
                "model": {
                    "type": "minecraft:model",
                    "model": f"{self.settings.namespace}:item/{self.id}"
                }
            }
        elif item == "gui":
            item = {
                "model": {
                    "type": "minecraft:select",
                    "property": "minecraft:display_context",
                    "cases": [
                        {
                            "when": "gui",
                            "model": {
                                "type": "minecraft:model",
                                "model": f"{self.settings.namespace}:item/{self.id}_gui"
                            }
                        }
                    ],
                    "fallback": {
                        "type": "minecraft:model",
                        "model": f"{self.settings.namespace}:item/{self.id}"
                    }
                }
            }
        write_json(item_path, item, self.settings.indent)

    def make_recipe(self, recipe):
        recipe_path = self.settings.get_path("recipe")
        result = {
            "count": recipe.get("count", 1),
            "id": self.base_item,
            "components": self.components
        }
        recipe["result"] = result
        recipe.pop("count", None)
        if "advancement" in recipe:
            self.make_recipe_advancement(recipe.get("advancement").get("trigger_item"))
            recipe.pop("advancement", None)

        path = Path(recipe_path / f"{self.id}.json")
        write_json(path, recipe, self.settings.indent)

    def make_recipe_advancement(self, trigger_item):
        recipe_advancement = self.settings.get_path("recipe_advancement") / f"{self.id}.json"

        advancement = {"parent": "minecraft:recipes/root", "criteria": {
            f"has_{trigger_item}": {"conditions": {"items": [{"items": trigger_item}]},
                                    "trigger": "minecraft:inventory_changed"},
            "has_the_recipe": {"conditions": {"recipe": f"{self.settings.namespace}:{self.id}"},
                               "trigger": "minecraft:recipe_unlocked"}},
                       "requirements": [["has_the_recipe", f"has_{trigger_item}"]],
                       "rewards": {"recipes": [f"{self.settings.namespace}:{self.id}"]}}

        write_json(recipe_advancement, advancement, self.settings.indent)

    def make_loot_table(self):
        loot_table = {"pools": [
            {"rolls": 1, "entries": [
                {"type": "minecraft:item", "name": self.base_item}],
             "functions": [{"function": "minecraft:set_components", "components": self.components}]}]}

        path = Path(self.settings.get_path("loot_table") / "items" / f"{self.id}.json")
        write_json(path, loot_table, self.settings.indent)

    def make_components(self):
        if self.settings.auto_id:
            self.data.setdefault("custom_data", {}).update({"id": self.id})

        if "custom_data" in self.data:
            self.make_custom_data()

        # if settings has common components key
        if self.settings.common_components:
            common_components = self.settings.common_components
            # if match key is not in common_components, just copy common components
            if "match" not in common_components:
                self.components.update(common_components)
            # otherwise, try to find the right components
            else:
                self.match_component()

        self.components.update(self.data.get("components", {}))
        self.components["minecraft:item_model"] = f"{self.namespace}:{self.id}"
        self.components["minecraft:item_name"] = {
            "translate": f"item.{self.namespace}.{self.id}"
        }

        if "lore" in self.data:
            if "minecraft:lore" not in self.components:
                self.components["minecraft:lore"] = []
            self.components["minecraft:lore"] = self.make_lore(self.data["lore"]) + self.components.get(
                "minecraft:lore", [])

    def match_component(self):
        fallback = self.settings.common_components.get("fallback")
        if "type" in self.data:
            self.components.update(self.settings.common_components.get("cases", {}).
                                   get(self.data.get("type"), fallback))
        else:
            # default components
            self.components.update(fallback.copy())  # Copy to avoid reference issues

    def make_custom_data(self):
        custom_data = self.data.get("custom_data", {})

        self.components.setdefault("minecraft:custom_data", {})[self.settings.namespace] = custom_data


def write_json(path, content, indentation):
    # Ensure the parent directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Write the JSON file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=indentation, ensure_ascii=False)

    print(f"Created ...{Path(*path.parts[-4:])}")


def check_templates(item, template):
    print(f"Using Template: {template}")

    # Deep copy the template before updating to prevent reference issues
    template_data = copy.deepcopy(item.settings.templates.get(template, {}))
    item.data.update(template_data)

    # Merge components separately to avoid shared references
    item.data['components'] = deep_merge(
        item.data.get('components', {}),
        template_data.get('components', {})  # Use the copied template
    )

    # If template is "block", update item.data instead of reassigning item
    if template == "block":
        resolved_data = resolve_placeholders(block(), item)
        item.data.update(resolved_data)  # Ensures we update instead of replacing item itself


def deep_merge(dict1, dict2):
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            # If both are dictionaries, merge them recursively
            dict1[key] = deep_merge(dict1[key], value)
        else:
            # Otherwise, just set/overwrite the value
            dict1[key] = value
    return dict1


def material():
    return {
        "base": "minecraft:poisonous_potato",
        "components": {
            "!minecraft:food": {},
            "!minecraft:consumable": {}
        },
        "item": "simple",
        "model": "minecraft:item/generated"
    }


def block():
    return {
        "base": "{{base}}",
        "components": {
            "minecraft:container": [
                {
                    "slot": 0,
                    "item": {
                        "id": "minecraft:structure_block",
                        "count": 1,
                        "components": {
                            "minecraft:custom_data": {
                                "{{namespace}}": {
                                    "placed_block": True,
                                    "block": "{{id}}"
                                }
                            },
                        }
                    }
                }
            ],
            "minecraft:block_entity_data": {
                "id": "{{base}}"
            },
            "minecraft:tooltip_display": {
                "hidden_components": [
                    "minecraft:container"
                ]
            }
        },
        "custom_data": {"custom_block": True}
    }


def resolve_placeholders(data, item):
    # Recursively replaces placeholders in keys and values of a dictionary.
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = key.replace("{{namespace}}", item.namespace).replace("{{id}}", item.id).replace("{{base}}",
                                                                                                      item.base_item)
            new_value = resolve_placeholders(value, item)
            new_dict[new_key] = new_value
        return new_dict
    elif isinstance(data, list):
        return [resolve_placeholders(value, item) for value in data]
    elif isinstance(data, str):
        return data.replace("{{namespace}}", item.namespace).replace("{{id}}", item.id).replace("{{base}}",
                                                                                                item.base_item)
    return data


def make_sprites(image_path):
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size

    # Ensure dimensions are multiples of 16
    assert width % 16 == 0 and height % 16 == 0, "Image dimensions must be multiples of 16."

    # Calculate number of textures in each dimension
    rows = height // 16
    cols = width // 16

    # Create a matrix to store textures
    texture_matrix = [[None for _ in range(cols)] for _ in range(rows)]

    # Extract each 16x16 texture
    for row in range(rows):
        for col in range(cols):
            left = col * 16
            upper = row * 16
            right = left + 16
            lower = upper + 16

            # Crop the texture
            texture = img.crop((left, upper, right, lower))

            # Check if the texture is fully transparent
            if all(pixel[3] == 0 for pixel in texture.getdata()):
                continue  # Skip fully transparent textures

            texture_matrix[row][col] = texture

    return texture_matrix


class Settings:
    def __init__(self, _settings):
        self.namespace = _settings.get("namespace", "item_gen")
        self.indent = _settings.get("meta", {}).get("indent", 4)
        self.common_components = _settings.get("common_components", None)
        self.order_lang = _settings.get("meta", {}).get("order_lang", None)
        self.auto_id = _settings.get("auto_id", False)

        self.datapack_folder = Path(_settings.get("datapack", None)).resolve()
        self.resourcepack_folder = Path(_settings.get("resourcepack", None)).resolve()

        if "spritesheet" in _settings:
            self.sprites = make_sprites(_settings.get("spritesheet"))
            print(self.sprites)
        else:
            self.sprites = None

        self.templates = {
            "material": material(),
            "block": block(),
        }

        if "templates" in _settings:
            self.templates_folder = Path(_settings.get("templates", None)).resolve()
            json_folder = self.templates_folder
            for json_file in json_folder.glob("*.json"):
                with open(json_file, "r", encoding="utf-8") as f:
                    try:
                        self.templates[json_file.stem] = json.load(f)  # Use file name (without .json) as key
                    except json.JSONDecodeError as e:
                        print(f"Error reading {json_file}: {e}")

        self.paths = {
            "inputs": Path(_settings.get("items", None)).resolve(),
            "datapack": self.datapack_folder,
            "resourcepack": self.resourcepack_folder,
            "loot_table": self.datapack_folder / f"data/{self.namespace}/loot_table",
            "recipe": self.datapack_folder / f"data/{self.namespace}/recipe",
            "recipe_advancement": self.datapack_folder / f"data/{self.namespace}/advancement/recipes",
            "items": self.resourcepack_folder / f"assets/{self.namespace}/items",
            "lang": self.resourcepack_folder / f"assets/{self.namespace}/lang/en_us.json",
            "models": self.resourcepack_folder / f"assets/{self.namespace}/models/item",
            "textures": self.resourcepack_folder / f"assets/{self.namespace}/textures/item"
        }

    def __str__(self):
        return (f"{self.namespace}:[\n\t" + "\n\t".join(f"{k}: {v}" for k, v in self.paths.items())
                + "\n]\n\tIndent: {self.indent},order_lang: {self.order_lang}")

    def get_path(self, key):
        return self.paths.get(key)


def build():
    with open(settings.get_path("lang"), encoding="utf-8", errors="surrogateescape") as f:
        lang = json.load(f)

    # Process each JSON file in the specified folder
    items_path = settings.get_path("inputs")
    for json_file in items_path.glob("*.json"):
        with open(json_file, encoding="utf-8") as f:
            try:
                print(f"> Processing {json_file.stem}...")
                data = json.load(f)
                item = Item(json_file.stem, data, lang, settings)
                item.make()
            except json.JSONDecodeError as e:
                print(f"Error decoding {json_file}: {e}")

    # Write the updated lang data back to the file, ensuring that escape sequences are preserved
    if settings.order_lang:
        lang = {k: lang[k] for k in sorted(lang)}
    with open(settings.get_path("lang"), "w", encoding="utf-8") as f:
        json.dump(lang, f, indent=settings.indent, ensure_ascii=True)


if __name__ == '__main__':
    settings = Settings(json.load(open("settings.json")))
    build()

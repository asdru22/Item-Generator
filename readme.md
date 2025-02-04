# `settings.json`

| Key                   | Value   | Explanation                                                                                                    | Example                                                                                        |
|-----------------------|---------|----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `"namespace"`         | string  | Datapack and resourcepack namespace                                                                            | `"my_pack"`                                                                                    |
| `"datapack"`          | path    | Path to the datapack folder                                                                                    | `"C:\User\Documents\my_pack\datapack"`                                                         |
| `"resourcepack"`      | path    | Path to the resourcepack folder                                                                                | `"C:\User\Documents\my_pack\resourcepack"`                                                     |
| `"items"`             | path    | Path to the `items.json` folder                                                                                | `"C:\User\Documents\my_pack\items"`                                                            |
| `"meta"`              | map     | Map containing information on how the generator should process certain data                                    | [See below](https://github.com/asdru22/Item-Generator/blob/master/readme.md#meta)              |
| `"common_components"` | map     | Indicates components that should be shared across all items (ie. lore, tooltip)                                | [See below](https://github.com/asdru22/Item-Generator/blob/master/readme.md#common_components) |
| `"auto_id"`           | boolean | If set to true, `the custom_data` component will have this data `{<namespace>:{"id":<id>}}`                    | `true`                                                                                         |
| `"templates"`         | path    | The path to the custom templates folder. The filename will become the key, and its content the actual template | See `material` and block `templates`                                                           |

## `meta`

| Key            | Value   | Explanation                                                      | Example |
|----------------|---------|------------------------------------------------------------------|---------|
| `"indent"`     | integer | Controls indentation of generated json files, defaults to 4      | 2       |
| `"order_lang"` | boolean | Indicates if the generated lang should be ordered alphabetically | `true`  |

## `common_components`

Common components can either be a normal component map

```json
{
  "minecraft:max_stack_size": 16,
  "minecraft:food": {
    "can_always_eat": true,
    "nutrition": 1,
    "saturation": 0.6
  }
}
```

Or a special structure can be used to search for conditions inside each item's json file.

```json
{
  "match": "type",
  "cases": {
    "cool": {
      "minecraft:lore": [
        {
          "text": "My Pack but cool",
          "color": "white",
          "italic": false
        }
      ]
    },
    "epic": {
      "minecraft:lore": [
        {
          "tex": "My pack but epic",
          "color": "white",
          "italic": false,
          "font": "haywire:main",
          "with": [
            {
              "translate": "pack.haywire"
            }
          ]
        }
      ]
    }
  },
  "fallback": {
    "minecraft:lore": [
      {
        "tex": "My pack",
        "color": "white",
        "italic": false
      }
    ]
  }
}
```

This will look for the `"type"` key inside each items `.json` file, and see if it matches with any of the values
provided in `"cases"`. If `"type"` is missing, it will default to the components present in `"fallback"`.

# Item`.json`

| Key             | Value             | Explanation                                                                                                             | Example                                                                             |
|-----------------|-------------------|-------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `"translation"` | string            | What the item's name should be translated to.                                                                           | `"My Cool Sword"`                                                                   |
| `"base"`        | string            | The base item used. defaults to `"minecraft:poisonous_potato"`                                                          | `"minecraft:diamond_sword"`                                                         |
| `"components"`  | map               | The item's components                                                                                                   | `{"minecraft:max_damage": 6}`                                                       |
| `"recipe"`      | map               | A variation of the item's crafting recipe                                                                               | [See below](https://github.com/asdru22/Item-Generator/blob/master/readme.md#recipe) |
| `"item"`        | `"simple"` or map | If `"simple"`, the basic item json will be generated. Otherwise an entire item model definition json can be pasted      | `"simple"` or https://misode.github.io/assets/item/                                 |
| `"model"`       | string or map     | If it's a string, it will generate a basic item model, where the value is the parent. Otherwise any model can be pasted | `"minecraft:item/generated"` or https://misode.github.io/assets/model/              |
| `"custom_data"` | map               | All data provided will be placed in `"minecraft:custom_data".<namespace>`                                               | `{uses_left:10}`                                                                    |
| `"template"`    | string            | Name of the template to use                                                                                             | `"material"`                                                                        |
| `"lore"`        | map               | Shorthand for adding lore with translated text                                                                          | [See below](https://github.com/asdru22/Item-Generator/blob/master/readme.md#lore)   |

## `"recipe"`

```json
{
  "type": "minecraft:crafting_shapeless",
  "count": 5,
  "category": "misc",
  "ingredients": [
    "minecraft:honey_bottle",
    "minecraft:sugar",
    "minecraft:resin_clump"
  ],
  "advancement": {
    "trigger_item": "minecraft:honey_bottle"
  }
}
```

In this variation of the recipe json, the `"result"` key is removed, and `"count"` is put as an optional key in the
root. If omitted it will default to 1.  
The `"advancement"` key is optional, and when present will create the advancement that will unlock the recipe when the
player has the `"trigger_item"` in their inventory.

## `"lore"`

A quick way to add lore, with text that is directly translated by being immediately added to the lang file with its
translation key.

```json
{
  "color": "green",
  "italic": false,
  "contents": [
    "My custom item",
    "is very cool"
  ]
}
```

for example this will generate an item with lore

```json
[
  {
    "translate": "item.<namespace>.<id>.lore0",
    "color": "green",
    "italic": false
  },
  {
    "translate": "item.<namespace>.<id>.lore1",
    "color": "green",
    "italic": false
  }
]

```

# What is *always* automatically generated?

- `item_name` component: item name translation keys will follow the `item.<namespace>.<id>` structure
- `item_model` component: item model keys will follow the `<namespace>:<id>` structure
- Loot tables: loot tables will generate at `<datapack_path>/data/<namespace>/loot_table/items/`
- `en_us.json` translation key and corresponding translation

# Templates

Templates are applied to items of the same category in order to avoid declaring the same properties.
The built-in templates are:

## `"material"`

```json
{
  "base": "minecraft:poisonous_potato",
  "components": {
    "!minecraft:food": {},
    "!minecraft:consumable": {}
  },
  "item": "simple",
  "model": "minecraft:item/generated"
}
```

## `"block""`

```json
{
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
                "placed_block": true,
                "block": "{{id}}"
              }
            }
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
  "custom_data": {
    "custom_block": true
  }
}
```

The block is a bit more complex, since values like the base item, namespace and id need to change based on the generator
and item settings.

# Custom templates

Json files inside the `"templates"` path specified in the `settings.json` file will be merged into the built-in
templates' dictionary,

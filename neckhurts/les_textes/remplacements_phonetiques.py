# Remplacements phonétiques pour la fonction mimic
# Chaque tuple contient (ancien_son, nouveau_son)

REMPLACEMENTS_PHONETIQUES = [
    # Sons [k]
    ("qu", "k"), ("que", "ke"), ("qui", "ki"), ("qua", "ka"),
    ("ch", "sh"), ("sch", "sh"),
    
    # Sons [s]
    ("ce", "se"), ("ci", "si"), ("ça", "sa"), ("ço", "so"),
    ("ss", "s"), ("sc", "s"),
    
    # Sons [z]
    ("s", "z"), ("x", "z"),
    
    # Sons [f]
    ("ph", "f"), ("ff", "f"),
    
    # Sons [j]
    ("ge", "je"), ("gi", "ji"), ("j", "g"),
    
    # Sons [an/en]
    ("an", "en"), ("en", "an"), ("em", "am"), ("am", "em"),
    
    # Sons [in/un]
    ("in", "un"), ("un", "in"), ("ain", "ein"), ("ein", "ain"),
    
    # Sons [ou]
    ("ou", "u"), ("oo", "u"),
    
    # Sons [é/è/ai]
    ("ai", "é"), ("ei", "é"), ("è", "é"), ("é", "ai"),
    ("et", "é"), ("er", "é"), ("ez", "é"),
    
    # Sons [o/au/eau]
    ("au", "o"), ("eau", "o"), ("ô", "o"), ("o", "au"),
    
    # Consonnes doubles
    ("ll", "l"), ("rr", "r"), ("nn", "n"), ("mm", "m"),
    ("tt", "t"), ("pp", "p"), ("dd", "d"), ("bb", "b"),
    
    # H muet
    ("th", "t"), ("rh", "r"), ("ph", "f"),
    
    # Autres confusions
    ("y", "i"), ("w", "v"), ("tion", "sion"),
]
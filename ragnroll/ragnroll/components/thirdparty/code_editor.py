import reflex as rx

class CodeEditor(rx.Component):

    library = "@monaco-editor/react"
    tag = "Editor"
    is_default = True

    default_value: rx.Var[str]
    default_language: rx.Var[str]
    height: rx.Var[str] = "30vh"
    width: rx.Var[str] = "100%"
    theme: rx.Var[str] = 'vs-dark'
    options: rx.Var[dict]
    on_change: rx.EventHandler[lambda value: [value]]

code_editor = CodeEditor.create

disable_intellisense = {
    "quickSuggestions": {
        "other": False,
        "comments": False,
        "strings": False,
    },
    "parameterHints": {"enabled": False},
    "ordBasedSuggestions": False,
    "suggestOnTriggerCharacters": False,
    "acceptSuggestionOnEnter": "off",
    "tabCompletion": "off",
    "wordBasedSuggestions": False,
}

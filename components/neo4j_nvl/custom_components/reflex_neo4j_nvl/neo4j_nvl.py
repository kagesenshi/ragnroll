import reflex as rx
from typing import TypedDict
from reflex.components.component import NoSSRComponent
from typing import Any, Optional

class GraphElement(TypedDict, total=False):
    id: str
    color: Optional[str]
    selected: Optional[bool]
    caption: Optional[str]  # Deprecated
    disabled: Optional[bool]
    hovered: Optional[bool]
    captionSize: Optional[int]
    captionAlign: Optional[str]  # 'top' | 'bottom' | 'center'

class Node(GraphElement, total=False):
    size: Optional[int]
    pinned: Optional[bool]
    x: Optional[float]
    y: Optional[float]
    activated: Optional[bool]
    icon: Optional[str]


class Relationship(GraphElement, total=False):
    id: str
    # Use string literal syntax to allow using reserved keywords
    from_: str  # used internally for referencing
    to: str
    type: Optional[str]
    width: Optional[float]

Relationship.__annotations__['from'] = Relationship.__annotations__.pop('from_')

class Point(TypedDict):
    x: float 
    y: float 

class ReactSyntheticEvent(TypedDict, total=False):
    bubbles: Optional[bool]
    cancelable: Optional[bool]
    defaultPrevented: Optional[bool]
    eventPhase: Optional[int]
    isTrusted: Optional[bool]
    timeStamp: Optional[float]
    type: Optional[str]

class MouseEvent(ReactSyntheticEvent, total=False):
    altKey: Optional[bool]
    button: Optional[int]
    buttons: Optional[int]
    clientX: Optional[int]
    clientY: Optional[int]
    ctrlKey: Optional[bool]
    metaKey: Optional[bool]
    movementX: Optional[int]
    movementY: Optional[int]
    offsetX: Optional[int]
    offsetY: Optional[int]
    pageX: Optional[int]
    pageY: Optional[int]
    screenX: Optional[int]
    screenY: Optional[int]
    shiftKey: Optional[bool]


class HitTargetNode(TypedDict):
    data: Node 
    targetCoordinates: Point 
    pointerCoordinates: Point 
    distanceVector: Point
    distance: float
    insideNode: bool

class HitTargetRelationship(TypedDict):
    data: Relationship
    fromTargetCoordinates: Point
    toTargetCoordinates: Point 
    pointerCoordinates: Point 
    distance: float

class HitTargets(TypedDict):
    nodes: list[HitTargetNode]
    relationships: list[HitTargetRelationship]

class Neo4jNVL(NoSSRComponent):
    library = f'/public/{rx._x.asset('asset')}'
    tag = 'InteractiveNvlWrapper'

    lib_dependencies: list[str] = [
        "@neo4j-nvl/react"
    ]

    nodes: rx.Var[list[Node]]
    rels: rx.Var[list[Relationship]]
    layout: rx.Var[str] = 'forcedirected'
    minimap_container: rx.Var[str] 

    on_hover : rx.EventHandler[lambda element, hit_targets, event: [element, hit_targets, event]] 
    on_node_click : rx.EventHandler[lambda node, hit_targets, event: [node, hit_targets, event]] 
    on_node_double_click : rx.EventHandler[lambda node, hit_targets, event: [node, hit_targets, event]] 
    on_node_right_click : rx.EventHandler[lambda node, hit_targets, event: [node, hit_targets, event]]
    on_relationship_click : rx.EventHandler[lambda rel, hit_targets, event: [rel, hit_targets, event]]
    on_relationship_double_click :  rx.EventHandler[lambda rel, hit_targets, event: [rel, hit_targets, event]]
    on_relationship_right_click :  rx.EventHandler[lambda rel, hit_targets, event: [rel, hit_targets, event]]
    on_canvas_click : rx.EventHandler[lambda event: [event]]
    on_canvas_right_click : rx.EventHandler[lambda event: [event]]
    on_pan : rx.EventHandler[lambda event: [event]]
    on_zoom : rx.EventHandler[lambda zoom_level: [zoom_level]]
    on_drag : rx.EventHandler[lambda nodes: [nodes]]
    on_drag_start : rx.EventHandler[lambda nodes, event: [nodes, event]]
    on_drag_end :  rx.EventHandler[lambda nodes, event: [nodes, event]]
    on_draw_started : rx.EventHandler[lambda event: [event]]
    on_draw_ended : rx.EventHandler[lambda new_rel, target_node, event: [new_rel, target_node, event]]
    on_hover_node_margin : rx.EventHandler[lambda node: [node]]
    on_box_started : rx.EventHandler[lambda event: [event]]
    on_box_select : rx.EventHandler[lambda elements, event: [elements, event]]
    on_lasso_started : rx.EventHandler[lambda event: [event]]
    on_lasso_select : rx.EventHandler[lambda hit_items, event: [hit_items, event]]
    

neo4j_nvl = Neo4jNVL.create
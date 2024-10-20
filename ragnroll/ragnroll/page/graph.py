from ..components.code_form import code_form
from ..components.util import main_template
from ..components.thirdparty.neo4j_nvl import Node, Relationship, neo4j_nvl, HitTargets, MouseEvent
import reflex as rx
import random

class State(rx.State):

    nodes: list[Node] 
    rels: list[Relationship] 
    id_counter: int = 1

    async def on_node_click(self, node: Node, hit_targets: HitTargets, event: MouseEvent):
        self.id_counter += 1
        self.nodes.append(Node({'id': f'{self.id_counter}'}))
        print(self.nodes)
        print(hit_targets)
        print(event)

    async def on_box_select(self, elements, event: MouseEvent):
        print(elements, event)

@rx.page(route='/graph')
def graph() -> rx.Component:
    return main_template(rx.box(
        neo4j_nvl(nodes=State.nodes, rels=State.rels, 
                        on_node_click=State.on_node_click,
                        on_box_select=State.on_box_select),
        width='100%', height='800px'))
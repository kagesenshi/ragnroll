import dynamic from 'next/dynamic';
import { jsx as _jsx } from "react/jsx-runtime";
import { BoxSelectInteraction, ClickInteraction, DragNodeInteraction, DrawInteraction, HoverInteraction, LassoInteraction, PanInteraction, ZoomInteraction } from '@neo4j-nvl/interaction-handlers';
import { forwardRef, memo, useEffect, useRef, useState } from 'react';
// const BasicNvlWrapper = dynamic(() => import('@neo4j-nvl/react').then((mod) => mod.BasicNvlWrapper), { ssr: false });
// const INTERACTIVE_WRAPPER_ID = dynamic(() => import('@neo4j-nvl/react/lib/utils/constants').then((mod) => mod.INTERACTIVE_WRAPPER_ID), { ssr: false });
// const destroyInteraction = dynamic(() => import('@neo4j-nvl/react/lib/interactive-nvl-wrapper/hooks').then((mod) => mod.destroyInteraction), { ssr: false });
// const useInteraction = dynamic(() => import('@neo4j-nvl/react/lib/interactive-nvl-wrapper/hooks').then((mod) => mod.useInteraction), { ssr: false });
import { BasicNvlWrapper } from '@neo4j-nvl/react';
import { INTERACTIVE_WRAPPER_ID } from '@neo4j-nvl/react/lib/interactive-nvl-wrapper/hooks';
import { destroyInteraction, useInteraction } from '@neo4j-nvl/react/lib/interactive-nvl-wrapper/hooks';
const options = {
    selectOnClick: false,
    drawShadowOnHover: true,
    selectOnRelease: false,
    excludeNodeMargin: true
};
/**
 * The interactive React wrapper component contains a collection of interaction handlers by default
 * and provides a variety of common functionality and callbacks.
 * It is an extension of the {@link BasicNvlWrapper} component and incorporates the
 * @neo4j-nvl/interaction-handlers module's decorators to provide a set of interaction events.
 *
 * The mouseEventCallbacks property takes an object where various callbacks can be defined
 * and behavior can be toggled on and off.
 *
 * For examples, head to the {@link https://neo4j.com/docs/nvl/current/react-wrappers/#_interactive_reactive_wrapperr Interactive React wrapper documentation page}.
 */
export const InteractiveNvlWrapper = memo(forwardRef(({ 
            nodes, rels, layout, layoutOptions, onInitializationError, 
            minimapContainer = null,
            onHover = null, 
            onNodeClick = null, 
            onNodeDoubleClick = null, 
            onNodeRightClick = null,
            onRelationshipClick = null,
            onRelationshipDoubleClick = null,
            onRelationshipRightClick = null,
            onCanvasClick = null,
            onCanvasRightClick = null,
            onPan = null,
            onZoom = null,
            onDrag = null,
            onDragStart = null,
            onDragEnd = null,
            onDrawStarted = null,
            onDrawEnded = null,
            onHoverNodeMargin = null,
            onBoxStarted = null,
            onBoxSelect = null,
            onLassoStarted = null,
            onLassoSelect = null,
            nvlCallbacks = {}, interactionOptions = options, 
            ...nvlEvents }, 
            nvlRef) => {
    const nvlOptions = {
        'minimapContainer': document.getElementById(minimapContainer),
        'allowDynamicMinZoom': true,
    }
    const [nodeState, setNodes] = useState(nodes);
    const newNvlRef = useRef(null);
    const myNvlRef = nvlRef ?? newNvlRef;
    const hoverInteraction = useRef(null);
    const clickInteraction = useRef(null);
    const panInteraction = useRef(null);
    const zoomInteraction = useRef(null);
    const dragNodeInteraction = useRef(null);
    const drawInteraction = useRef(null);
    const multiSelectInteraction = useRef(null);
    const lassoInteraction = useRef(null);
    useInteraction(HoverInteraction, hoverInteraction, onHover, 'onHover', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onNodeClick, 'onNodeClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onNodeDoubleClick, 'onNodeDoubleClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onNodeRightClick, 'onNodeRightClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onRelationshipClick, 'onRelationshipClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onRelationshipDoubleClick, 'onRelationshipDoubleClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onRelationshipRightClick, 'onRelationshipRightClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onCanvasClick, 'onCanvasClick', myNvlRef, interactionOptions);
    useInteraction(ClickInteraction, clickInteraction, onCanvasRightClick, 'onCanvasRightClick', myNvlRef, interactionOptions);
    useInteraction(PanInteraction, panInteraction, onPan, 'onPan', myNvlRef, interactionOptions);
    useInteraction(ZoomInteraction, zoomInteraction, onZoom, 'onZoom', myNvlRef, interactionOptions);
    useInteraction(DragNodeInteraction, dragNodeInteraction, onDrag, 'onDrag', myNvlRef, interactionOptions);
    useInteraction(DragNodeInteraction, dragNodeInteraction, onDragStart, 'onDragStart', myNvlRef, interactionOptions);
    useInteraction(DragNodeInteraction, dragNodeInteraction, onDragEnd, 'onDragEnd', myNvlRef, interactionOptions);
    useInteraction(DrawInteraction, drawInteraction, onHoverNodeMargin, 'onHoverNodeMargin', myNvlRef, interactionOptions);
    useInteraction(DrawInteraction, drawInteraction, onDrawStarted, 'onDrawStarted', myNvlRef, interactionOptions);
    useInteraction(DrawInteraction, drawInteraction, onDrawEnded, 'onDrawEnded', myNvlRef, interactionOptions);
    useInteraction(BoxSelectInteraction, multiSelectInteraction, onBoxStarted, 'onBoxStarted', myNvlRef, interactionOptions);
    useInteraction(BoxSelectInteraction, multiSelectInteraction, onBoxSelect, 'onBoxSelect', myNvlRef, interactionOptions);
    useInteraction(LassoInteraction, lassoInteraction, onLassoStarted, 'onLassoStarted', myNvlRef, interactionOptions);
    useInteraction(LassoInteraction, lassoInteraction, onLassoSelect, 'onLassoSelect', myNvlRef, interactionOptions);
    useEffect(() => () => {
        destroyInteraction(hoverInteraction);
        destroyInteraction(clickInteraction);
        destroyInteraction(panInteraction);
        destroyInteraction(zoomInteraction);
        destroyInteraction(dragNodeInteraction);
        destroyInteraction(drawInteraction);
        destroyInteraction(multiSelectInteraction);
        destroyInteraction(lassoInteraction);
    }, []);
    return (_jsx(BasicNvlWrapper, { ref: myNvlRef, nodes: nodes, id: INTERACTIVE_WRAPPER_ID, rels: rels, nvlOptions: nvlOptions, nvlCallbacks: nvlCallbacks, layout: layout, layoutOptions: layoutOptions, onInitializationError: onInitializationError, ...nvlEvents }));
}));

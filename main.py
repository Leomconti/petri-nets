import xml.etree.ElementTree as ET
import time
from random import randint
from typing import List, Dict
import threading
from concurrent.futures import ThreadPoolExecutor
import graphviz
import os

class Place:
    def __init__(self, id: str, label: str, marking: int = 0, x: int = 0, y: int = 0):
        self.id = id
        self.label = label
        self.marking = marking
        self.position = [x, y]
        self.offset = [0, 0]
        self.semaphore = threading.Semaphore(1)
    
    def add_tokens(self, count: int):
        with self.semaphore:
            self.marking += count

    def remove_tokens(self, count: int):
        with self.semaphore:
            if self.marking >= count:
                self.marking -= count
                return True
            return False

    def __str__(self):
        return f"{self.label} (tokens: {self.marking})"

class Transition:
    def __init__(self, id: str, label: str, x: int = 0, y: int = 0):
        self.id = id
        self.label = label
        self.position = [x, y]
        self.offset = [0, 0]
        self.input_arcs = []
        self.output_arcs = []

    def add_input_arc(self, arc):
        self.input_arcs.append(arc)

    def add_output_arc(self, arc):
        self.output_arcs.append(arc)

    def is_enabled(self):
        return all(arc.source.marking >= arc.weight for arc in self.input_arcs)

    def fire(self):
        if not self.is_enabled():
            return False

        # Remove tokens from input places
        for arc in self.input_arcs:
            if not arc.source.remove_tokens(arc.weight):
                return False

        # Add tokens to output places
        for arc in self.output_arcs:
            arc.target.add_tokens(arc.weight)

        return True

    def __str__(self):
        return self.label

class Arc:
    def __init__(self, id: str, source, target, weight: int = 1, arc_type: str = 'normal'):
        self.id = id
        self.source = source
        self.target = target
        self.weight = weight
        self.type = arc_type

    def __str__(self):
        return f"{self.source} --> {self.target} (weight: {self.weight})"

class PetriNet:
    def __init__(self):
        self.id = f"PetriNet{str(time.time())}{str(randint(0, 1000))}"
        self.name = ""
        self.places: Dict[str, Place] = {}
        self.transitions: Dict[str, Transition] = {}
        self.arcs: List[Arc] = []

    def add_place(self, place: Place):
        self.places[place.id] = place

    def add_transition(self, transition: Transition):
        self.transitions[transition.id] = transition

    def add_arc(self, arc: Arc):
        self.arcs.append(arc)
        if isinstance(arc.source, Place):
            if isinstance(arc.target, Transition):
                arc.target.add_input_arc(arc)
            else:
                print(f"Warning: Invalid arc {arc.id} from Place to Place")
        elif isinstance(arc.source, Transition):
            if isinstance(arc.target, Place):
                arc.source.add_output_arc(arc)
            else:
                print(f"Warning: Invalid arc {arc.id} from Transition to Transition")
        else:
            print(f"Warning: Invalid arc {arc.id} with unknown source type")

    def get_enabled_transitions(self):
        return [t for t in self.transitions.values() if t.is_enabled()]

    def __str__(self):
        text = f"--- Net: {self.name}\nTransitions: "
        text += " ".join(str(t) for t in self.transitions.values())
        text += "\nPlaces: "
        text += " ".join(str(p) for p in self.places.values())
        text += "\nArcs:\n"
        text += "\n".join(str(a) for a in self.arcs)
        text += "\n---"
        return text

class PetriNetSimulator:
    def __init__(self, petri_net: PetriNet, max_iterations: int):
        self.petri_net = petri_net
        self.max_iterations = max_iterations
        self.iteration = 0
        self.graph = graphviz.Digraph(comment=f'Petri Net: {petri_net.name}')
        self.graph.attr(rankdir='LR')
        self.thread_count = 0
        self.thread_lock = threading.Lock()
        self.draw_thread = None

    def simulate(self):
        # self.draw_net_async()
        while self.iteration < self.max_iterations:
            enabled_transitions = self.petri_net.get_enabled_transitions()
            if not enabled_transitions:
                print(f"No more enabled transitions. Simulation ended at iteration {self.iteration}.")
                break

            print(f"\nIteration {self.iteration + 1}:")
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.fire_transition, t) for t in enabled_transitions]
                for future in futures:
                    future.result()

            self.iteration += 1
            self.print_state()
            # self.draw_net_async()

        print("\nSimulation completed.")
        if self.draw_thread:
            self.draw_thread.join()  # Wait for the last drawing to complete

    def draw_net_async(self):
        if self.draw_thread:
            self.draw_thread.join()  # Wait for the previous drawing to complete
        self.draw_thread = threading.Thread(target=self.draw_net)
        self.draw_thread.start()

    def fire_transition(self, transition: Transition):
        with self.thread_lock:
            self.thread_count += 1
            thread_id = self.thread_count
        
        if transition.fire():
            print(f"Thread {thread_id}: Fired transition: {transition}")
        else:
            print(f"Thread {thread_id}: Failed to fire transition: {transition}")

    def print_state(self):
        print("Current state:")
        for place in self.petri_net.places.values():
            print(f"  {place}")

    def draw_net(self):
        self.graph.clear()
        for place in self.petri_net.places.values():
            self.graph.node(place.id, f"{place.label}\n({place.marking})", shape='circle')
        for transition in self.petri_net.transitions.values():
            self.graph.node(transition.id, transition.label, shape='rect')
        for arc in self.petri_net.arcs:
            self.graph.edge(arc.source.id, arc.target.id, label=str(arc.weight))
        
        output_dir = 'petri_net_images'
        os.makedirs(output_dir, exist_ok=True)
        self.graph.render(f'{output_dir}/petri_net_step_{self.iteration}', format='png', cleanup=True)

def parse_pnml(file_path: str) -> List[PetriNet]:
    tree = ET.parse(file_path)
    root = tree.getroot()
    nets = []

    for net_node in root.findall(".//net"):
        petri_net = PetriNet()
        petri_net.id = net_node.get('id', petri_net.id)  # type: ignore
        name_node = net_node.find(".//name/text")
        petri_net.name = name_node.text if name_node is not None else petri_net.id  # type: ignore

        for place_node in net_node.findall(".//place"):
            place_id = place_node.get('id')  # type: ignore
            name_node = place_node.find(".//name/text")
            label = name_node.text if name_node is not None else place_id  # type: ignore
            marking_node = place_node.find(".//initialMarking/text")
            marking = int(marking_node.text) if marking_node is not None else 0  # type: ignore
            graphics = place_node.find(".//graphics/position")
            x, y = 0, 0
            if graphics is not None:
                x = int(float(graphics.get('x', 0)))
                y = int(float(graphics.get('y', 0)))
            place = Place(place_id, label, marking, x, y) # type: ignore
            petri_net.add_place(place)

        for transition_node in net_node.findall(".//transition"):
            transition_id  = transition_node.get('id')  # type: ignore
            name_node = transition_node.find(".//name/text")
            label = name_node.text if name_node is not None else transition_id  # type: ignore
            graphics = transition_node.find(".//graphics/position")
            x, y = 0, 0
            if graphics is not None:
                x = int(float(graphics.get('x', 0)))
                y = int(float(graphics.get('y', 0)))
            transition = Transition(transition_id, label, x, y) # type: ignore
            petri_net.add_transition(transition)

        for arc_node in net_node.findall(".//arc"):
            arc_id = arc_node.get('id')  
            source_id = arc_node.get('source')  
            target_id = arc_node.get('target')  
            inscription_node = arc_node.find(".//inscription/text")
            weight = int(inscription_node.text) if inscription_node is not None else 1  # type: ignore
            arc_type = arc_node.get('type', 'normal')  

            source = petri_net.places.get(source_id) or petri_net.transitions.get(source_id)  # type: ignore
            target = petri_net.places.get(target_id) or petri_net.transitions.get(target_id)  # type: ignore

            if source is not None and target is not None:
                arc = Arc(arc_id, source, target, weight, arc_type) # type: ignore
                petri_net.add_arc(arc)
            else:
                print(f"Warning: Invalid arc {arc_id} from {source_id} to {target_id}")

        nets.append(petri_net)

    return nets

def main():
    # file_path = input("Enter the path to the .pnml file: ")
    file_path = "teste4.pnml"
    # max_iterations = int(input("Enter the maximum number of iterations: "))
    max_iterations = 25

    petri_nets = parse_pnml(file_path)
    
    for i, net in enumerate(petri_nets, 1):
        print(f"\nSimulating Petri Net {i}:")
        print(net)
        simulator = PetriNetSimulator(net, max_iterations)
        simulator.simulate()

if __name__ == "__main__":
    main()
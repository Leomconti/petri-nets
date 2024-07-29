import xml.etree.ElementTree as ET
import threading
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

class Place:
    def __init__(self, id: str, name: str, tokens: int = 0):
        self.id = id
        self.name = name
        self.tokens = tokens
        self.semaphore = threading.Semaphore(1)

    def add_tokens(self, count: int):
        with self.semaphore:
            self.tokens += count

    def remove_tokens(self, count: int):
        with self.semaphore:
            if self.tokens >= count:
                self.tokens -= count
                return True
            return False

class Transition:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.input_arcs = []
        self.output_arcs = []
        self.semaphore = threading.Semaphore(1)

    def add_input_arc(self, arc):
        self.input_arcs.append(arc)

    def add_output_arc(self, arc):
        self.output_arcs.append(arc)

    def is_enabled(self):
        return all(arc.source.tokens >= arc.weight for arc in self.input_arcs)

    def execute(self):
        with self.semaphore:
            if self.is_enabled():
                for arc in self.input_arcs:
                    if not arc.source.remove_tokens(arc.weight):
                        return False
                for arc in self.output_arcs:
                    arc.target.add_tokens(arc.weight)
                return True
            return False

class Arc:
    def __init__(self, id: str, source, target, weight: int = 1):
        self.id = id
        self.source = source
        self.target = target
        self.weight = weight
class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = {}
        self.global_lock = threading.Lock()

    def add_place(self, place: Place):
        with self.global_lock:
            self.places[place.id] = place

    def add_transition(self, transition: Transition):
        with self.global_lock:
            self.transitions[transition.id] = transition

    def add_arc(self, arc: Arc):
        with self.global_lock:
            self.arcs[arc.id] = arc
            if isinstance(arc.source, Place):
                if isinstance(arc.target, Transition):
                    arc.target.add_input_arc(arc)
                else:
                    raise ValueError("Arc from Place must go to a Transition")
            elif isinstance(arc.source, Transition):
                if isinstance(arc.target, Place):
                    arc.source.add_output_arc(arc)
                else:
                    raise ValueError("Arc from Transition must go to a Place")
            else:
                raise ValueError("Invalid arc: source must be either Place or Transition")


    def get_enabled_transitions(self) -> List[Transition]:
        with self.global_lock:
            return [t for t in self.transitions.values() if t.is_enabled()]

    def print_net(self):
        with self.global_lock:
            print("Petri Net:")
            print("Places:")
            for place in self.places.values():
                print(f"  Place ID: {place.id}, Name: {place.name}, Tokens: {place.tokens}")
            print("Transitions:")
            for transition in self.transitions.values():
                print(f"  Transition ID: {transition.id}, Name: {transition.name}")
            print("Arcs:")
            for arc in self.arcs.values():
                print(f"  Arc ID: {arc.id}, Source: {arc.source.id}, Target: {arc.target.id}, Weight: {arc.weight}")

class PetriNetExecutor:
    def __init__(self, petri_net: PetriNet, iterations: int):
        self.petri_net = petri_net
        self.iterations = iterations
        self.execution_lock = threading.Lock()
        self.state_change = threading.Condition(self.execution_lock)

    def execute(self):
        with ThreadPoolExecutor() as executor:
            for i in range(self.iterations):
                print(f"\nIteration {i + 1}:")
                enabled_transitions = self.petri_net.get_enabled_transitions()
                futures = [executor.submit(self.execute_transition, transition) for transition in enabled_transitions]
                
                for future in futures:
                    future.result()  # Wait for all transitions to complete

                with self.execution_lock:
                    self.print_network_state()

    def execute_transition(self, transition: Transition):
        if transition.execute():
            print(f"Executed transition: {transition.name}")

    def print_network_state(self):
        print("Network state:")
        for place in self.petri_net.places.values():
            print(f"  {place.name}: {place.tokens} tokens")

def parse_pnml(file_path: str) -> PetriNet:
    tree = ET.parse(file_path)
    root = tree.getroot()
    petri_net = PetriNet()

    for place in root.findall(".//place"):
        id = place.get('id')
        name = place.find('name/text').text if place.find('name/text') is not None else id # type: ignore
        initial_marking = int(place.find('initialMarking/text').text) if place.find('initialMarking/text') is not None else 0 # type: ignore
        petri_net.add_place(Place(id, name, initial_marking)) # type: ignore

    for transition in root.findall(".//transition"):
        id = transition.get('id')
        name = transition.find('name/text').text if transition.find('name/text') is not None else id # type: ignore
        petri_net.add_transition(Transition(id, name)) # type: ignore

    for arc in root.findall(".//arc"):
        id = arc.get('id')
        source_id = arc.get('source')
        target_id = arc.get('target')
        weight = int(arc.find('inscription/text').text) if arc.find('inscription/text') is not None else 1 # type: ignore

        source = petri_net.places.get(source_id) or petri_net.transitions.get(source_id)
        target = petri_net.places.get(target_id) or petri_net.transitions.get(target_id)

        petri_net.add_arc(Arc(id, source, target, weight)) # type: ignore

    return petri_net

def main():
    # file_path = input("Enter the path to the .pnml file: ")
    file_path = "example.pnml"
    # iterations = int(input("Enter the number of iterations: "))
    iterations = 50

    petri_net = parse_pnml(file_path)
    print(petri_net.print_net())
    executor = PetriNetExecutor(petri_net, iterations)
    executor.execute()

if __name__ == "__main__":
    main()
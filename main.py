import xml.etree.ElementTree as ET
import time
from random import randint
from typing import List, Dict

class Place:
    def __init__(self, id: str, label: str, marking: int = 0, x: int = 0, y: int = 0):
        self.id = id
        self.label = label
        self.marking = marking
        self.position = [x, y]
        self.offset = [0, 0]
    
    def add_tokens(self, count: int):
        ...
    def remove_tokens(self, count: int):
        ...

    def __str__(self):
        return f"{self.label} (tokens: {self.marking})"

class Transition:
    def __init__(self, id: str, label: str, x: int = 0, y: int = 0):
        self.id = id
        self.label = label
        self.position = [x, y]
        self.offset = [0, 0]

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

    def __str__(self):
        text = f"--- Net: {self.name}\nTransitions: "
        text += " ".join(str(t) for t in self.transitions.values())
        text += "\nPlaces: "
        text += " ".join(str(p) for p in self.places.values())
        text += "\nArcs:\n"
        text += "\n".join(str(a) for a in self.arcs)
        text += "\n---"
        return text

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
    file_path = "example.pnml"
    petri_nets = parse_pnml(file_path)

    for i, net in enumerate(petri_nets, 1):
        print(f"\nPetri Net {i}:")
        print(net)

if __name__ == "__main__":
    main()
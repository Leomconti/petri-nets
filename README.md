# Diagrama de classes

```mermaid
classDiagram
    class Place {
        -String id
        -String name
        -int tokens
        +addTokens(int)
        +removeTokens(int)
    }
    class Transition {
        -String id
        -String name
        +execute()
    }
    class Arc {
        -String id
        -int weight
    }
    class Marking {
        -Map~Place, int~ markings
        +setMarking(Place, int)
        +getMarking(Place)
    }
    class PetriNet {
        -List~Place~ places
        -List~Transition~ transitions
        -List~Arc~ arcs
        -Marking marking
        +addPlace(Place)
        +addTransition(Transition)
        +addArc(Arc)
        +setInitialMarking(Marking)
    }
    class PetriNetExecutor {
        -PetriNet petriNet
        -int iterations
        +execute()
        -executeTransition(Transition)
    }
    PetriNet "1" -- "*" Place
    PetriNet "1" -- "*" Transition
    PetriNet "1" -- "*" Arc
    PetriNet "1" -- "1" Marking
    Arc "1" -- "1" Place
    Arc "1" -- "1" Transition
    PetriNetExecutor "1" -- "1" PetriNet
```

# Diagrama de sequencia

```mermaid
sequenceDiagram
    participant Main
    participant PetriNetExecutor
    participant PetriNet
    participant Transition
    participant Place
    participant Marking

    Main->>PetriNetExecutor: execute()
    loop n iterations
        PetriNetExecutor->>PetriNet: getEnabledTransitions()
        PetriNet->>Transition: isEnabled()
        Transition->>Place: getTokens()
        Place-->>Transition: tokens
        Transition-->>PetriNet: enabled status
        PetriNet-->>PetriNetExecutor: enabled transitions

        par Execute enabled transitions
            PetriNetExecutor->>Transition: execute()
            Transition->>Place: removeTokens()
            Transition->>Place: addTokens()
        end

        PetriNetExecutor->>PetriNet: updateMarking()
        PetriNet->>Marking: setMarking()
        PetriNetExecutor->>Main: Print executed transitions and network state
    end
```

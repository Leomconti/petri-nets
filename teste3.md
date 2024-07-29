```mermaid
graph TD
    subgraph P0 [Place P0]
        p0_token1((1)):::token
    end
    subgraph P1 [Place P1]
        p1_token0((0)):::token
    end
    subgraph P2 [Place P2]
        p2_token0((0)):::token
    end
    subgraph P3 [Place P3]
        p3_token0((0)):::token
    end
    subgraph P4 [Place P4]
        p4_token0((0)):::token
    end
    
    P0 -->|1| T1[Transition T1]
    T1 -->|1| P1
    P1 -->|1| T2[Transition T2]
    T2 -->|1| P2
    P2 -->|1| T3[Transition T3]
    T3 -->|1| P3
    P3 -->|1| T4[Transition T4]
    T4 -->|1| P4

    P1 -->|1| T3
    P4 -->|1| T2
    T1 -->|1| P2

    classDef token fill:#f9f,stroke:#333,stroke-width:2px;
```
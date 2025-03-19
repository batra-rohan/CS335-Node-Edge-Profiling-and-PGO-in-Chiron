:outer = 3
:inner = 2
:x = 10

repeat :outer [
    :y = 5
    repeat :inner [
        forward :y
        :y = :y + 5
        if (:x > 15) [
            right 90
        ] else [
            left 45
        ]
    ]
    :x = :x + 5
]
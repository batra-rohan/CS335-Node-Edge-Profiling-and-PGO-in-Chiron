:x = 10
:y = 20
:z = 5
:p = 0
:q = 50

pendown

repeat 5 [
    :x = :x + 5
    if (:x > 20) [
        :y = :y - 5
        goto (100, 100)
    ] else [
        forward :y
    ]

    repeat 3 [
        :z = :z + 2
        if (:z < 10) [
            right 45
            forward :z
        ] else [
            left 30
            :p = :p + 10
            forward :p
        ]
    ]
]

penup
goto (0, 0)

repeat 4 [
    :q = :q - 10
    if (:q > 20) [
        forward :q
        right 90
    ] else [
        left 45
        backward :q
    ]
]
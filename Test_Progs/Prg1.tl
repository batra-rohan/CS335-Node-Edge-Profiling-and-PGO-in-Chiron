:x = 10
:y = 5

repeat 3 [
    :x = :x + 5
    if (:x > 15) [
        :y = :y + 10
        goto (100, 50)
    ] else [
        forward :y
    ]
]
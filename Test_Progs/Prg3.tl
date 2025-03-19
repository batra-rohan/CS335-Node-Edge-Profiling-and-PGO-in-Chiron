:x = 20
:y = 30
:count = 0

repeat 6 [
    if (:count < 3) [
        forward :x
        right 45
    ] else [
        forward :y
        left 45
    ]
    :count = :count + 1
]
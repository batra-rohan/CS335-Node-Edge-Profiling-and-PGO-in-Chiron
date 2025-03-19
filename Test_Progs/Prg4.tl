:steps = 50
:angle = 30

repeat 5 [
    forward :steps
    right :angle
    :steps = :steps - 5
    if (:steps < 20) [
        goto (0, 0)
    ]
]
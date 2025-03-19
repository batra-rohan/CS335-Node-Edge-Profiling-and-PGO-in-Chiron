:side = 50
:counter = 0

repeat 4 [
    forward :side
    right 90
    if (:counter == 2) [
        goto (0, 0)
    ]
    :counter = :counter + 1
]
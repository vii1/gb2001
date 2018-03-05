'''Misc utility functions'''

def smoothstep( edge0, edge1, x ):
    x = min( max( x, 0.0 ), 1.0 )
    return edge0 + (edge1-edge0) * (x*x*x*(x*(x*6 - 15) + 10))



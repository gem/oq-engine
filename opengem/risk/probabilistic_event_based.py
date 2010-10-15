# -*- coding: utf-8 -*-

from opengem import shapes

def compute_loss_ratios(vuln_function, ground_motion_field):
    """Compute loss ratio using the ground motion field passed."""
    if vuln_function == shapes.EMPTY_CURVE or not ground_motion_field:
        return []
    
    imls = vuln_function.abscissae
    loss_ratios = []
    
    # seems like with numpy you can only specify a single fill value
    # if the x_new is outside the range. Here we need two different values,
    # depending if the x_new is below or upon the defined values
    for ground_motion_value in ground_motion_field:
        if ground_motion_value < imls[0]:
            loss_ratios.append(0.0)
        elif ground_motion_value > imls[-1]:
            loss_ratios.append(imls[-1])
        else:
            loss_ratios.append(vuln_function.ordinate_for(
                    ground_motion_value))
    
    return loss_ratios

import time
from rotary_irq_rp2 import RotaryIRQ

r = RotaryIRQ(pin_num_clk=18,
              pin_num_dt=19,
              min_val=0,
              max_val=5,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)

val_old = r.value()
while True:
    val_new = r.value()

    if val_old != val_new:
        val_old = val_new
        print('result =', val_new)

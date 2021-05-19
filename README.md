# Neuromorphic Intelligence CPG project

## Software Setup

### Getting the GUI to run on Zemo

Set the DISPLAY variable in Windows Terminal

```
setx DISPLAY localhost:0.0
```

SSH into Zemo with X11 forwarding enabled

```
ssh -Y <user>@zemo.lan.ini.uzh.ch
# or add the following two lines to the SSH config file in VSCode
ForwardX11 yes
ForwardX11Trusted yes
```

It should be possible to run GUI applications in the terminal

```
xeyes
```

But currently, this doesn't work - get the following error after opening the device with `gui=True`. The visualiser window pops up, but it seems samna can't connect to it to update the visualisation?

```
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/class_NI2021/CPG/Dynapse1Utils.py", line 98, in open_dynapse1
    gui_process, gui_receiving_port = open_gui(store, device_name, visualizer_id)
  File "/home/class_NI2021/CPG/Dynapse1Utils.py", line 147, in open_gui
    samna.open_remote_node(visualizer_id, viz_name)
RuntimeError: Store with ID: 3 timed out on content request
```

## Hardware Notes

Onchip connections from left chips (i.e. 0,2) to right chips (i.e. 1,3) will make chips die. NetworkGenerator.py:53

Having a different number of connections from the same neuron to 2 different neurons will cause the network verification to fail. Eg. n0 -> n1 (2 times) and n0 -> n2 (3 times). Unclear if this is a limitation of the chip, or a bug with the network generator code. NetworkGenerator.py:303
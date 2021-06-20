# Neuromorphic Intelligence CPG project

## Software Setup

### Installing ctxctl_contrib and dynapse_wrapper

Run the following to install ctxctl_contrib and dynapse_wrapper locally with pip, so Python can find them easily.

```
python3 -m pip install --editable ctxctl_contrib/
python3 -m pip install --editable dynapse_wrapper/
```

## Hardware Notes

Onchip connections from left chips (i.e. 0,2) to right chips (i.e. 1,3) will make chips die. Can therefore only implement two coupled CPG units (each need 3 cores).

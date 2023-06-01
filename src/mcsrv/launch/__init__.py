from .launch import LaunchMethod, LaunchMethodManager

from .forge import ForgeLaunchMethod
from .jar import JarLaunchMethod

LaunchMethodManager.register(JarLaunchMethod)
LaunchMethodManager.register(ForgeLaunchMethod)

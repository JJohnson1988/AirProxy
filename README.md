# AirProxy
AirProxy is a Python-based broker daemon that translates IPP communication between network printers and Apple devices running modern versions of macOS/iOS.

Long story short, Apple broke a lot of older printers starting with recent OS versions (like iOS 17). They became a lot more picky about mDNS records and how their devices communicate with network-based printers. Unfortunately, they never told anyone what they did, and many device manufacturers haven't released updated printer firmware to match new requirements. So, this fixes that disconnect (without any help from Apple).

**IMPORTANT**: *You still need some sort of custom mDNS/Avahi service file to pair with this script, assuming your current multicast broadcast service is also incompatible. I've included a sample Avahi service, but yours needs to fit (relatively) closely with your specific printer!*

It's also possible you don't need the proxy script at all, and all you need is an updated mDNS service file! If that's the case, your situation and solution has become a lot simpler.

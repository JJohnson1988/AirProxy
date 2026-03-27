# AirProxy
AirProxy is a Python-based broker daemon that translates IPP communication between network printers and Apple devices running modern versions of macOS/iOS.

Long story short, Apple broke a lot of older printers starting with recent OS versions (like iOS 17). They became a lot more picky about mDNS records and how their devices communicate with network-based printers. Unfortunately, they never told anyone what they did, and many device manufacturers have not released updated printer firmware to match new requirements. So, this fixes that disconnect (without any help from Apple).

**IMPORTANT**: *You still need some sort of custom mDNS/Avahi service file to pair with this script, assuming your current multicast broadcast service is also incompatible. I have included a sample Avahi service file, but yours needs to fit (relatively) closely with your specific printer!*

It is also possible you do not need the proxy script at all, and all you need is an updated mDNS service file! If that is the case, your situation and solution has become a lot simpler...

*Some final notes:* 

Ultimately the proxy script is just a "dumb" pipe that listens on the IPP port and pretty much forwards whatever it receives to the printer. However, some printers will not appreciate the fact that the incoming data does not contain the correct host information in the header payload.

In order to solve that, you would need to upgrade from this basic proxy to something that can intercept the data and rewrite the header information. A situation like that is more of a job for a full-featured reverse proxy, such as Nginx.

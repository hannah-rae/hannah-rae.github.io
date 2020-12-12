---
title: "Integrating Novelty Detection Capabilities with MSL Mastcam Operations to Enhance Data Analysis"
collection: publications
permalink: /publication/2021-ieee-aero-novelty
excerpt: 
date: 2021-03-06
venue: IEEE Aerospace Conference
paperurl: 
citation: 'Horton, P., Kerner, H., Jacobs, S., Cisneros, E., Wagstaff, K. L., and Bell III, J. F. (2021). &quot;Integrating Novelty Detection Capabilities with MSL Mastcam Operations to Enhance Data Analysis.&quot; <i>IEEE Aerospace Conference</i>.'

---

While innovations in scientific instrumentation have pushed the boundaries of Mars rover mission capabilities, the increase in data complexity has pressured Mars Science Laboratory (MSL) and future Mars rover operations staff to quickly analyze complex data sets to meet progressively shorter tactical and strategic planning timelines. 
MSLWEB is an internal data tracking tool used by operations staff to perform first pass analysis on MSL image sequences, a series of products taken by the Mast camera, Mastcam. Mastcam consists of a pair of 400-1000 nm wavelength cameras on MSL's Remote Sensing Mast that, among other functions, uses a filter wheel to produce multispectral images by creating a sequence of products at different wavelengths. 
Mastcam's multiband multispectral image sequences require more complex analysis compared to standard 3-band RGB images. 
Typically, these are analyzed by the inspection of false color images created to aid visualization, such as band ratios between different spectral indices that can highlight specific potential mineralogic differences among iron-bearing phases, and decorrelation stretches to enhance the color differences between multiple filters. Given the short time frame of tactical planning in which downlinked images might need to be analyzed (within 5-10 hours before the next uplink), there exists a need to triage analysis time to focus on the most important sequences and parts of a sequence. 
We address this need by creating products for MSLWEB that use novelty detection to help operations staff identify unusual data that might be diagnostic of new or atypical compositions or mineralogies detected within an imaging scene. 
This was achieved in two ways: 1) by creating products for each sequence to identify novel regions in the image, and 2) by assigning multispectral sequences a sortable novelty score. 
These new products provide colorized heat maps of inferred novelty that operations staff can use to rapidly review downlinked data and focus their efforts on analyzing potentially new kinds of diagnostic multispectral signatures. 
This approach has the potential to guide scientists to new discoveries by quickly drawing their attention to often subtle variations not detectable with simple color composites.
The products developed in this work have shown promising benefits for integration into mission operations by potentially decreasing tactical operations planning time through guided triage.

<!-- [Download paper here](https://gabrieltseng.github.io/assets/pubs/kenya_crop_mapping.pdf)
 -->
Recommended citation: Horton, P., Kerner, H., Jacobs, S., Cisneros, E., Wagstaff, K. L., and Bell III, J. F. (2021). &quot;Integrating Novelty Detection Capabilities with MSL Mastcam Operations to Enhance Data Analysis.&quot; <i>IEEE Aerospace Conference</i>.
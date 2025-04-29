<img src="./holo/assets/images/holo_logo.png" alt="Holo Logo - Generated with Dalle" width="200"/>

# What is Holo?

Holo is my Computer Engineering capstone project at Bellarmine University. See the project absract below:
<br>

Project Holo is a multimodal artificial intelligence (AI) system that integrates multiple AI technologies into a dynamic, hand-gesture-controlled canvas painting and image generation application. With the increasing integration of AI in consumer applications, Holo provides users with an intuitive and interactive platform for AI-driven image creation. 

Holo is written in python but can be compiled down to C code for slightly increased performance. The graphical user interface (GUI) utilizes a library called “tkinter” with a custom theme wrapper called “custom tkinter.” Holo users can create a sketch using drawing tools such as a pen brush, fill tool, transform, and rectangle tool, and/or enter a text-based image generation prompt. Upon initiating the "Generate AI Image" function, Holo processes the provided inputs via an API call, using a variety of selectable AI models which convert the sketch and/or prompt into an image that appears in the designated output tab.

Holo supports standard interaction methods, including keyboard, mouse, and tablet pen input. Additionally, it enhances user engagement by incorporating a projector-interface and in-app hand tracking using MediaPipe – a Google solution suite enabling hand tracking and pose estimation in real time video feeds.  The local hand position of a user in frame, derived from the MediaPipe hand solution, is mapped to screen space to control the on-screen cursor, while gesture-based controls — such as pinching the index finger and thumb to emulate a mouse press — enable a seamless, touch-free interaction experience. This innovative approach makes Holo a versatile tool for AI-assisted digital art creation, expanding the possibilities of human-computer interaction in creative applications.


# Download the Report, Poster, or Abstract Below


[Report](https://github.com/zaccowan/Holo/blob/main/Holo%20Project%20Report.pdf)


[Poster](https://github.com/zaccowan/Holo/blob/main/Holo%20Poster%20Presentation.pdf)


[Abstract](https://github.com/zaccowan/Holo/blob/main/Holo%20Abstract.pdf)

[Quick Video Presentation](https://video.bellarmine.edu/media/Holo+Video+Presentation/1_d3lplo8q)



# Running Holo

1. Clone the project to your machine.
2. Run the following in a terminal from the root directory of the repository:
   
   Setup Environment and Install Dependencies
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   
   Navigate to the holo application director and run the holo entry point - holo.py.
   ```
   cd holo
   python holo.py
   ```

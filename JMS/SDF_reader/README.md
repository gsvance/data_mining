# SDF_reader
A kludgey way to read SDF files

Less a library or reader program proper and more of a template for how to read SDF files
manually. It's not hard, as you can see it takes maybe 50 lines of code including white space
and readability breaks. The worst part of using it is having to inspect the file you wish to 
read, sicne not many people even have hex editiors installed these days. 

Eventually I will add some basic header sense so you have to do less hand jiggering of things,
but really this project is just an interim to figuring out the sdf reader library proper and
writing a wury generator around that. Unil then, this is a good starting point. 

~Jack M. Sexton - 2015

Update: Now calculates the number of objects in the file correctly and works for
all data-sets conforming to the particle declared. Please inspect the dataset being opened
first and confirm it is is correct. If changes need to made you'll need the header length 
and structure declaration of the new file as well as changes to the for loops as applicable. 
~JMS 3/12/2015

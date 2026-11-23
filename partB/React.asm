
// Draws a rectangle at the top-left corner
// Height is stored in R0
// Width is 16 pixels

@R0
D=M
@END
D;JLE

@SCREEN
D=A
@address
M=D

(LOOP)
    @address
    A=M
    M=-1

    @address
    D=M
    @32
    D=D+A
    @address
    M=D

    @R0
    MD=M-1
    @LOOP
    D;JGT

(END)
    @END
    0;JMP

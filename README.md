
# ssh-copy-id

A Python implementation of [ssh-copy-id](https://linux.die.net/man/1/ssh-copy-id) that works on **ALL** platforms.

## Dependencies

[Fabric](http://www.fabfile.org/) : A Python (3.x) library and command-line tool for streamlining the use of SSH for application deployment or systems administration tasks.

[Nuitka ](https://nuitka.net/) : Nuitka is the optimizing Python compiler written in Python that creates executables that run without a separate installer. Data files can both be included or put alongside.
```
poetry install
```

## Build
```cmd
poetry run nuitka --onefile --standalone --output-dir=dist --output-filename=ssh-copy-id.exe ssh-copy-id.py
```

## Usage

```
ssh-copy-id.py [-h] [-i [IDENTITY_FILE]] [-p [PORT]] [user@]machine
```

For Windows users, there is a pre-built *exe* executable file (only tested on Windows 7 64-bit) under ```dist```.

## License
[MIT License](https://zhengyi.mit-license.org/@2017)  
&copy; Zhengyi Yang   
&copy; pedoc  
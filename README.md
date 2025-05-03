Installation Guide
Prerequisites
Python: Make sure you have Python 3.7 or higher installed on your system. You can download Python from python.org.
Java: Make sure Java is installed on your system since the script involves executing a .jar file. You can download Java from Oracle's website or use OpenJDK.
Step 1: Install Required Libraries
Open your terminal (Command Prompt, PowerShell, or Terminal) and install required Python packages using pip:
``` bash
pip install pyrogram TgCrypto
```
Step 2: Obtain API Credentials
Create a new bot on Telegram:
Message @BotFather on Telegram.
Use the command /newbot and follow the instructions. Save the provided API token.
Obtain your API ID and API Hash:
Go to the Telegram API development tools.
Log in with your phone number and then create a new application. Note down your API ID and API hash.
Step 3: Modify the Script
Download the script to your local machine.
Open the script file in your favorite text editor.
Replace YOUR_OWNER_USER_ID with your actual Telegram user ID. You can find your user ID by using a bot that returns your user ID, such as @userinfobot.
Ensure that the paths for JAR_PATH, RULES_FILE, and MAPPING_FILE are correctly set based on your environment.
Step 4: Run the JAR File
Make sure the JAR file you intend to use (protect.jar) is placed in the path you defined in JAR_PATH. Ensure that it is executable and that you have the required permissions.

Step 5: Run the Script
Open a terminal in the directory where your script is located.
Run the script using the following command:
``` bash
python protect.py
```
Replace your_script_name.py with the actual filename of your Python script.

Step 6: Interact with the Bot
Open your Telegram app and locate your bot by its name.
Start a chat with the bot and upload the APK file along with the required convertRules.txt file to process it.
Additional Notes
Dependencies: Make sure that all dependencies (Python packages and Java) are properly installed and that you can execute Java commands via terminal/command line.
Permissions: Depending on your operating system, you might need to grant appropriate permissions to access the directory where the script and files are located.
Output Directory: Ensure that the BUILD_OUTPUT_DIR specified in the script is writable by the bot. If needed, change the permissions accordingly.
Troubleshooting
If you encounter errors about missing modules, confirm that you have installed all required Python packages.
If the bot does not respond, check the API token and ensure it's correct.
Review permissions if the bot cannot write to directories.
Always check for errors printed in the console to help with troubleshooting issues.

# nmmp
基于dex-vm运行dalvik字节码从而对dex进行保护，增加反编译难度。
项目分为两部分nmm-protect是纯java项目，对dex进行转换，把dex里数据转为c结构体，opcode随机化生成ndk项目,编译后生成加固后的apk。nmmvm是一个安卓项目，包含dex-vm实现及各种dalvik指令的测试等。
# nmm-protect

+ 配置ndk及环境变量

不编译nmm-protect，可以直接看使用它生成项目及最后的apk，[一个对apk处理的例子](https://github.com/maoabc/nmmp/releases/download/demo/demo.zip)。

例子在linux环境下测试的，windows也应该没问题,先安装好JDK及android sdk和ndk。

下载[vm-protect.jar](https://github.com/maoabc/nmmp/releases/download/last/vm-protect-2023-07-08-0942.jar),配置好环境变量ANDROID_SDK_HOME、ANDROID_NDK_HOME:
``` bash
export ANDROID_HOME=/root/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.4
export PATH=$PATH:$ANDROID_HOME/ndk/24.0.8215888
export ANDROID_NDK_ROOT=$ANDROID_HOME/ndk/24.0.8215888
```
+ apk加固
  
``` bash
java -jar vm-protect-xxx.jar apk input.apk convertRules.txt mapping.txt
```
执行完毕会在input.apk所在的目录下生成一个build目录，里面包含最后输出的apk(build/input-protect.apk)，完整的c项目dex2c(基于cmake)及处理过程中生成的.dex等。  
第一次运行后会在jar位置生成tools目录，里面有config.json可以编辑它配置安卓sdk，ndk相关路径。

有朋友写了个GUI界面，能更方便使用，需要的可以去试试，https://github.com/TimScriptov/nmmp

生成的apk需要使用zipalign对齐（新版本已使用zipflinger处理apk,可以不用使用单独的zipalign）及apksigner签名才能安装使用
``` bash
apksigner sign --ks ~/.myapp.jks build/input-protect-align.apk
```
+ aab加固
  
``` bash
java -jar vm-protect-xxx.jar aab test.aab convertRules.txt
```
之后需要使用jarsigner签名，也可以集成signflinger进行签名
``` bash
jarsigner -keystore ~/.myapp.jks -storepass pass -keypass pass test-protect.aab keyAlias
```

+ aar加固
``` bash
java -jar vm-protect-xxx.jar aar testModule.aar convertRules.txt
```

+ 下载及编译项目
``` bash
git clone https://github.com/maoabc/nmmp.git
cd nmmp/nmm-protect
./gradlew arsc:build
./gradlew build
cd build/libs
mv vm-protect-xxx.jar protect.jar ##Rename to protect.jar
```
成功后会在build/libs生成可直接执行的fatjar。
+ 需要转换的类和方法规则

无转换规则文件，则会转换dex里所有class里的方法（除了构造方法和静态初始化方法）。规则只支持一些简单的情况：
``` java
//支持的规则比较简单，*只是被转成正则表达式的.*，支持一些简单的继承关系
class * extends android.app.Activity
class * implements java.io.Serializable
class my.package.AClass
class my.package.* { *; }
class * extends java.util.ArrayList {
  if*;
}


class A {
}
class B extends A {
}
class C extends B {
}
//比如'class * extends A' 只会匹配B而不会再匹配C
```


# nmmvm
nmmvm是dex虚拟机具体实现，入口就一个函数:
``` c
jvalue vmInterpret(
        JNIEnv *env,
        const vmCode *code,
        const vmResolver *dvmResolver
);

typedef struct {
    const u2 *insns;             //指令
    const u4 insnsSize;          //指令大小
    regptr_t *regs;                    //寄存器
    u1 *reg_flags;               //寄存器数据类型标记,主要标记是否为对象
    const u1 *triesHandlers;     //异常表
} vmCode;


typedef struct {

    const vmField *(*dvmResolveField)(JNIEnv *env, u4 idx, bool isStatic);

    const vmMethod *(*dvmResolveMethod)(JNIEnv *env, u4 idx, bool isStatic);

    //从类型常量池取得类型名
    const char *(*dvmResolveTypeUtf)(JNIEnv *env, u4 idx);

    //直接返回jclass对象,本地引用需要释放引用
    jclass (*dvmResolveClass)(JNIEnv *env, u4 idx);

    //根据类型名得到class
    jclass (*dvmFindClass)(JNIEnv *env, const char *type);

    //const_string指令加载的字符串对象
    jstring (*dvmConstantString)(JNIEnv *env, u4 idx);

} vmResolver;

```
vmCode提供执行所需要的指令、异常表及寄存器空间，vmResolver包含一组函数指针，提供运行时的符号，比如field，method等。通过自定义这两个参数来实现不同的加固方式，比如项目里的test.cpp有一个简单的基于libdex实现的vmResolver，它主要用于开发测试。而nmm-protect实现的是把.dex相关数据转换为c结构体，还包含了opcode随机化等，基本可实际使用。

# aar模块加固
目前已实现模块相关加固，用法同apk加固类似，如果有问题可以提issue。


# Licences
nmm-protect 以gpl协议发布,[nmm-protect licence](https://github.com/maoabc/nmmp/blob/master/nmm-protect/LICENSE), dex-vm部分以Apache协议发布, [nmmvm licence](https://github.com/maoabc/nmmp/blob/master/nmmvm/LICENSE). 只有vm部分会打包进apk中, nmm-protect只是转换dex,协议不影响生成的结果.

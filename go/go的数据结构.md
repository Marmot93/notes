## golang

对go语言每个人都有不同的了解，聊聊天，一起读读源码和官方文档

了解一下面试者是不是有扎实的基础或者较强的好奇心，乐于去了解更深层次的东西

关键词：设计原理，数据结构，日常应用

### 基本数据结构

#### 1. string

```go
package main

type StringHeader struct {
	Data uintptr
	Len  int
}
```

字符串拼接的原理

#### 2. array

    编译之后直接读写内存，处理越界，工程上用的很少，解题用的多一点点

#### 3. slice

```go
package main

type slice struct {
	array unsafe.Pointer
	len   int
	cap   int
}
```

    unsafe.Pointer 和 uintptr 的区别
    
    array unsafe.Pointer 会导致的一些问题
    
    slice的拷贝：编译期间拷贝还是运行时拷贝，两种拷贝方式都会通过 runtime.memmove 
    将整块内存的内容拷贝到目标的内存区域中

#### 4. map

[哈希表 hmap](https://github.com/golang/go/blob/41d8e61a6b9d8f9db912626eb2bbc535e929fefc/src/runtime/map.go#L115)

[桶 bmap](https://github.com/golang/go/blob/ac0ba6707c1655ea4316b41d06571a0303cc60eb/src/runtime/map.go#L149)

    【设计探讨】
    开放寻址法 和 拉链法
    【语言设计】
    Go 语言使用拉链法来解决哈希碰撞的问题实现了哈希表，
    它的访问、写入和删除等操作都在编译期间转换成了运行时的函数或者方法。
    哈希在每一个桶中存储键对应哈希的前 8 位，当对哈希进行操作时，
    这些 tophash 就成为可以帮助哈希快速遍历桶中元素的缓存。
    【扩容】
    哈希表的每个桶都只能存储 8 个键值对，一旦当前哈希的某个桶超出 8 个，
    新的键值对就会存储到哈希的溢出桶中。随着键值对数量的增加，
    溢出桶的数量和哈希的装载因子也会逐渐升高，超过一定范围就会触发扩容，
    扩容会将桶的数量翻倍，元素再分配的过程也是在调用写操作时增量进行的，
    不会造成性能的瞬时巨大抖动。

### function

1. 通过堆栈传递参数，入栈的顺序是从右到左，而参数的计算是从左到右；
2. 函数返回值通过堆栈传递并由调用者预先分配内存空间；
3. 调用函数时都是传值，接收方会对入参进行复制再计算；

#### 1. 参数传递

    C 语言的方式能够极大地减少函数调用的额外开销，但是也增加了实现的复杂度；
        CPU 访问栈的开销比访问寄存器高几十倍3；
        需要单独处理函数参数过多的情况；
    Go 语言的方式能够降低实现的复杂度并支持多返回值，但是牺牲了函数调用的性能；
        不需要考虑超过寄存器数量的参数应该如何传递；
        不需要考虑不同架构上的寄存器差异；
        函数入参和出参的内存空间需要在栈上进行分配；

    go语言使用栈作为参数和返回值传递的方法是综合考虑后的设计，选择这种设计意味着编译器会更加简单、更容易维护。

#### 2. 传递参数时是传值还是传引？

    Go 语言选择了传值的方式，无论是传递基本类型、结构体还是指针，都会对传递的参数进行拷贝。
    【struct】
    传递结构体时：会拷贝结构体中的全部内容；
    传递结构体指针时：会拷贝结构体指针；
    【uintptr】
    将指针作为参数传入某个函数时，函数内部会复制指针
    也就是会同时出现两个指针指向原有的内存空间，所以 Go 语言中传指针也是传值。
    so：
    在传递数组或者内存占用非常大的结构体时，我们应该尽量使用指针作为参数类型来避免发生数据拷贝进而影响性能。

### interface
    结构体和指针实现接口的区别：
```go
type Duck interface {
	Quack()
}

type Cat struct{}

func (c *Cat) Quack() {
	fmt.Println("meow")
}

func main() {
	var c Duck = Cat{}
	c.Quack()
}

$ go build interface.go
./interface.go:20:6: cannot use Cat literal (type Cat) as type Duck in assignment:
	Cat does not implement Duck (Quack method has pointer receiver)
```
    ↑为什么结构体指针实现接口初始化用结构体的时候会失败？

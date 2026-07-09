package ui

import "github.com/lxn/walk"

// stringListModel 是一个简单的字符串列表模型，供 ListBox 使用。
// 此版本 walk 未内置 StringListModel，故自行实现 walk.ListModel 接口。
type stringListModel struct {
	walk.ListModelBase
	items []string
}

func newStringListModel(items ...string) *stringListModel {
	return &stringListModel{items: items}
}

func (m *stringListModel) ItemCount() int {
	return len(m.items)
}

func (m *stringListModel) Value(index int) interface{} {
	return m.items[index]
}

// SetItems 替换全部条目并通知视图刷新
func (m *stringListModel) SetItems(items []string) {
	m.items = items
	m.PublishItemsReset()
}

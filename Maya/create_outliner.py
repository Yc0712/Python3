import maya.cmds as cmds

outline_dict = {
    "Matchmove":
        ["Camera",
         "Locators",
         "Scence",
         "Reference",
         {"ABC": ["Moving_object",
                  ]
          }]
}

"""
另一种方法
def create_outliner(nodes, parent=None):
    if isinstance(nodes, str):
        nodes = [nodes]
    for node in nodes:
        if isinstance(node, str):
            cmds.createNode("transform", name=node, parent=parent)
        elif isinstance(node, dict):
            for k, v in node.items():
                new_parent = cmds.createNode("transform", name=k, parent=parent)
                create_outliner(v, new_parent)
"""


class Create_mm_Outliner(object):
    """
    根据一个字典递归创建大纲
    """

    @classmethod
    def create_hierarchy(cls, data, out_parent=None):
        for k, v in data.items():  # 遍历一个字典
            ctrate_parent = cmds.createNode("transform", name=k, parent=out_parent)  # 将字典的key设置为父级
            if isinstance(v, list):  # 如果键是一个列表便利每个列表
                for child in v:
                    if isinstance(child, str):  # 便利每个列表查询是否是字符串
                        cmds.createNode("transform", name=child, parent=ctrate_parent)  # 如果是字符串就直接创建 父=字典的key
                    if isinstance(child, dict):  # 如果是一个字典
                        cls.create_hierarchy(child, out_parent=ctrate_parent)  # 运用递归将父设置为创建的key 重复
            if isinstance(v, str):  # 如果是字符串就直接创建
                cmds.createNode("transform", name=v, parent=ctrate_parent)  # 父=字典的key
            if isinstance(v, dict):
                cls.create_hierarchy(v, out_parent=ctrate_parent)  # 如果键还是一个字典那么就将他的父设置为K的父
        cmds.select(cl=True)
        return True


if __name__ == '__main__':
    Create_mm_Outliner.create_hierarchy(outline_dict)

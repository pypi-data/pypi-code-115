__all__ = ["register_sizeof"]


def register_sizeof(sizeof):
    @sizeof.register_lazy("awkward")
    def register_awkward():
        import awkward.highlevel
        
        @sizeof.register(awkward.highlevel.Array)
        def sizeof_ak_generic(obj):
            return obj.nbytes
    
    
    @sizeof.register_lazy("uproot")
    def register_uproot():
        import uproot.model

        @sizeof.register(uproot.model.Model)
        def sizeof_uproot_generic(obj):
            return obj.num_bytes

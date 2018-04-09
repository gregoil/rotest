========================
Blocks code architecture
========================

Background
==========

The blocks design paradigm was created to avoid code duplication and enable
composing tests faster.

``TestBlock`` is a building block for tests, commonly responsible for a single
action or a small set of actions.
It inherits from :mod:`unittest`'s :class:`TestCase <unittest.TestCase>`,
enabling it test-like behavior (``self.skipTest``, ``self.assertEqual``,
``self.fail``, etc.), and the Rotest infrastructure expands its behavior to
also be function-like (to have "inputs" and "outputs").

``TestFlow`` is a test composed of ``TestBlock`` instances (or other sub-test
flows), passing them their 'inputs' and putting them together, enabling them
to share data between each other.
A ``TestFlow`` can lock resources much like Rotest's TestCase, which it
passes to all the blocks under it.

The flow's final result depends on the result of the blocks under it by the
following order:

* If some block had an error, the flow ends with an error.
* If some block had a failure, the flow ends with a failure.
* Otherwise, the flow succeeds.

See also ``mode`` in the ``TestBlock``'s "Features" segment below for more
information about the run mechanism of a ``TestFlow``.

Features
========

TestFlow
--------

#. ``blocks``: static list or tuple of the blocks' classes of the flow. You
   can parametrize blocks in this section, in order to pass data to them (see
   `Sharing data`_ section or explanation in the TestBlock features section).

#. Rotest's ``TestCase`` features: run delta, filter by tags, running in
   multiprocess, TIMEOUT, etc. are available also for ``TestFlow`` class.

TestBlock
---------

#. ``inputs``: define a static list or tuple in the new block's class of fields
   the block needs to run. For example, defining in the block's scope

   .. code-block:: python

       class DemoBlock(TestBlock):
           inputs = ('field_name', 'other_field')
       ...

   will validate that the block instance will have all those field before
   running the parent flow.
   The inputs validation (which happens before running the topmost flow) passes
   if those fields are present in the block (e.g. the fields were set using
   parametrize), or if a previous sibling component will share those fields in
   runtime.

#. ``outputs``: define a static list or tuple in the new block's class of
   fields the block would share in its run. For example, defining in the
   block's scope

   .. code-block:: python

       class DemoBlock(TestBlock):
           outputs = ('field_name', 'other_field')
       ...

   means declaring that the block would calculate and share (using the
   ``share_data`` method) those fields, so that components following the block
   would get those fields at runtime.
   Declaring inputs and outputs of blocks is not mandatory, but it's a good way
   to make sure that the blocks "click" together properly, and no block will be
   missing fields at runtime.

Common features (for both flows and blocks)
-------------------------------------------

#. ``resources``: you can specify resources for the test flow or block, just
   like in Rotest's TestCase class.
   The resources of a flow will automatically propagate to the components under
   it.

#. ``parametrize`` (also ``params``): used to pass values to blocks or
   sub-flows, see example in the `Sharing data`_ section.
   Note that calling ``parametrize()`` or ``params()`` doesn't actually
   instantiate the component, but just saves values to be passed to it when it
   will be run.

#. ``mode``: this field can be defined statically in the component's class or
   passed to the instance using 'parametrize' (parametrized fields override
   class fields of blocks, since they are injected into the instance).
   Blocks and sub-flows can run in one of the following modes (which are
   defined in :mod:`rotest.core.flow_component`)

   #. ``MODE_CRITICAL``: upon failure or error, end the flow's run, skipping
      the following components (except those with mode ``MODE_FINALLY``).
      Use this mode for blocks or sub-flows that do actions that are mandatory
      for the continuation of the test.
   #. ``MODE_OPTIONAL``: upon error only, end the flow's run, skipping the
      following components (except those with mode ``MODE_FINALLY``). Use this
      mode for block or sub-flows that are not critical for the continuation of
      the test (since a failure in them doesn't stop the flow).
   #. ``MODE_FINALLY``: components with this mode aren't skipped even if the
      flow has already failed and stopped. Upon failure or error, end the
      flow's run, skipping the following components (except those with mode
      ``MODE_FINALLY``).
      Use this mode for example in blocks or sub-flows that do cleanup actions
      (which we should always attempt), much like things you would normally put
      in 'tearDown' of tests.

#. ``request_resources``: blocks and flows can dynamically request resources,
   calling ``request_resources(requests)`` method (see Rotest tutorial and
   documentation for more information).

   Since those are dynamic requests, don't forget to release those resources
   when they are not needed by calling

   .. code-block:: python

       release_resources(
           <dict of the dynamically locked resources, name: instance>)

   Resources can be locked locally and globally in regarding to the containing
   flow, i.e. by locking the resources using the parent's method:

   .. code-block:: python

       self.parent.request_resources(requests)

   The parent flow and all the sibling components would also have them.

Sharing data
------------

Sharing data between blocks (getting inputs and passing outputs) is crucial to
writing simple, manageable, and independent blocks.
Passing data to blocks (for them to use as 'inputs' parameters for the block's
run, much like arguments for a function) can be done in one of the following
methods:

* Locking resources - the resources the flow locks are injected into its
  components' instances (note that blocks can also lock resources, but they
  don't propagate them up or down).
  E.g. if a flow locks a resource with name 'res1', then all its components
  would have the field 'res1' which points to the locked resource.

* Sharing data - if one block writes somewhere in its test method:

  .. code-block:: python

      self.share_data(field_name=value)

  then all the components under the parent flow are injected (into their
  instance - self) where the field ``field_name`` is with value ``value``.

* Setting initial data to the test flow - you can set initial data to the
  components of flows by writing:

  .. code-block:: python

      class DemoFlow(TestFlow):
          common = {'field_name': 5,
                    'other_field': 'abc'}
      ...

  This will inject ``field_name=5`` and ``other_field='abc'`` as fields of the flow and
  its components before starting its run, so the blocks would also have access
  to those fields.
  This is the same as sharing those fields at the beginning of the flow's setUp
  method, using ``share_data()``.

* Using parametrize - you can specify fields for blocks or flows by calling
  their 'parametrize' class method.

  For example:

  .. code-block:: python

      class DemoFlow(TestFlow):
          blocks = (DemoBlock,
                    DemoBlock.parametrize(field_name=5,
                                          other_field='abc'))

  will create two blocks under the ``DemoFlow``, one ``DemoBlock`` block with
  the default values for ``field_name`` and ``other_field`` (which can be set
  by defining them as class fields for the block for example, see optional
  inputs and fields section), and a second ``DemoBlock`` with ``field_name=5``
  and ``other_field='abc'`` injected into the block instance (at runtime).

Example
-------

.. code-block:: python

    class DoSomethingBlock(TestBlock):
        """A block that does something.

        Attributes:
            resource1 (object): resource the block uses.
            input2 (object): input for the block.
            optional3 (object): optional input for the block.
        """
        mode = MODE_CRITICAL
        inputs = ('resource1', 'input2')

        optional3 = 0

        def test_method(self):
            """Do something."""
            self.logger.info("Doing something")
            self.resource1.do_something(self.input2, self.optional3)

    ...

    class DemoFlow(TestFlow):
        """Demo test-flow."""
        resource1 = SomeResourceClass(some_limitation=LIMITATION)

        common = {'input2': INPUT_VALUE}

        blocks = (DemoBlock1,
                  DemoBlock2,
                  DemoBlock1,
                  DoSomethingBlock.params(optional3=5),
                  DoSomethingBlock,
                  DemoBlock1.params(mode=MODE_FINALLY))

Sub-flows
---------

A flow may contain not only test-block, but also test-flows under it. This
feature can be used to wrap together blocks that tend to come together and also
to create sub-procedures (if a test block is comparable to a simple
function - it may have inputs and outputs and does a simple action, then a
sub-flow can be considered a complex function, which invokes other simpler
functions).
Note that a sub-flow behaves exactly like a block, meaning, you can call
parametrize on it, set a mode to it, it can't be filtered or skipped with
delta, etc.
This can give extra flexibility when composing flows with complex scenarios,
for example:

.. code-block:: none

    Flow
    |___BlockA
    |___BlockB
    |___BlockC
    |___BlockD

If you want that block B will only run if block A passed, and that block D will
only run if block C passed, but also to keep A and C not dependent, doing so is
impossible without the usage of sub flows.
But the scenario can be coded in the following manner:

.. code-block:: none

    Flow
    |___SubFlow1 (mode optional)
        |___BlockA (mode critical)
        |___BlockB (mode critical)
    |___SubFlow2 (mode optional)
        |___BlockC (mode critical)
        |___BlockD (mode critical)

Anonymous test-flows
--------------------

Sub-flows can be created on-the-spot using the 'create_flow' function, to avoid
defining classes.
The functions gets the following arguments:

* ``blocks`` - list of the flow's components.

* ``name`` - name of the flow, default value is "AnonymousTestFlow", but it's
  recommended to override it.

* ``mode`` - mode of the new flow.
  Either ``MODE_CRITICAL``, ``MODE_OPTIONAL`` or ``MODE_FINALLY``. Default is
  ``MODE_CRITICAL``.

* ``common`` - dict of initial fields and values for the new flow, same as the
  class variable 'common', default is empty dict.

.. code-block:: python

    from rotest.core.flow import TestFlow, create_flow

    class DemoFlow(TestFlow):
        """Demo test-flow."""
        resource1 = SomeResourceClass(some_limitation=LIMITATION)

        blocks = (DemoBlock1,
                  DemoBlock2,
                  DemoBlock1,
                  create_flow(name="TestSomethingFlow",
                              common={"input2": "value1"}
                              mode=MODE_OPTIONAL,
                              blocks=[DoSomethingBlock,
                                      DoSomethingBlock.params(optional3=5)]),
                  create_flow(name="TestSomethingFlow",
                              common={"input2": "value2"}
                              mode=MODE_OPTIONAL,
                              blocks=[DoSomethingBlock,
                                      DoSomethingBlock.params(optional3=5)]),
                  DemoBlock1.params(mode=MODE_FINALLY))


Optional inputs and fields
--------------------------

Mainly for convenience purposes, we sometimes want to have default values for
fields of blocks (inputs), just like we want default values for functions'
arguments.
Doing so is possible using the fact that passing inputs to blocks is done by
injecting fields into their instance.
For example:

.. code-block:: python

    class DemoBlock(TestBlock):
        """Demo block.

        Attributes:
            argument1 (number): block's first argument.
            argument2 (number): block's second argument.
            argument3 (number): block's third argument.
        """
        mode = MODE_CRITICAL
        inputs = ('argument1', 'argument2', 'argument3')

        argument2 = 0  # Setting default value to 0
        argument3 = 1  # Setting default value to 1

        def test_method(self):
            ...

Defining the block so is equivalent to defining the following function:

.. code-block:: python

    def DemoBlock(argument1, argument2=0, argument3=1):
        ...

Doing so, means that you wouldn't have to pass values to the block for the
parameters 'argument2' and 'argument3' (on ways of passing values to block's
parameters, see the `Sharing data`_ section), meaning that all the following
instantiations wouldn't raise an error due to input validation:

.. code-block:: python

    DemoBlock.params(argument1=5)  # arguments = 5,0,1
    DemoBlock.params(argument1=5,argument2=3)  # arguments = 5,3,1
    DemoBlock.params(argument1=5,argument3=4)  # arguments = 5,0,4
    DemoBlock.params(argument1=5,argument2=3,argument3=6)  # arguments = 5,3,6
